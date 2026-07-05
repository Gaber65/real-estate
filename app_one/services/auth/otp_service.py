# -*- coding: utf-8 -*-
import logging

from odoo import fields
from datetime import timedelta

from ...helpers.exceptions import (
    OTPCooldownError,
    OTPRateLimitExceeded,
    OTPExpiredError,
    OTPInvalidError,
    OTPMaxAttemptsExceeded,
    OTPSendFailedError,
    ValidationError,
)
from ...helpers.rate_limiter import RateLimiter
from ..providers.sms.sms_provider_factory import SMSProviderFactory

_logger = logging.getLogger(__name__)

# Defaults — all overridable via ir.config_parameter so ops can tune
# without a deploy. See _get_config().
DEFAULT_OTP_EXPIRY_MINUTES = 5
DEFAULT_OTP_LENGTH = 6
DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_RESEND_COOLDOWN_SECONDS = 60
DEFAULT_RATE_LIMIT_PER_HOUR = 5


class OTPService:
    """Owns the entire OTP lifecycle: generation, hashing, expiry,
    attempt-limiting, resend cooldown, and rate limiting.

    Deliberately does NOT depend on any specific SMS provider — it only
    talks to SMSProviderFactory, which returns something implementing
    BaseSMSProvider. Swapping Twilio for Vonage is a config change, not
    a code change here.
    """

    def __init__(self, env):
        self.env = env
        self.otp_model = env['real_estate.otp']
        self.icp = env['ir.config_parameter'].sudo()

    # ------------------------------------------------------------------
    # Config (all tunable via ir.config_parameter)
    # ------------------------------------------------------------------
    def _get_config(self):
        return {
            'expiry_minutes': int(self.icp.get_param('real_estate.otp_expiry_minutes', DEFAULT_OTP_EXPIRY_MINUTES)),
            'code_length': int(self.icp.get_param('real_estate.otp_length', DEFAULT_OTP_LENGTH)),
            'max_attempts': int(self.icp.get_param('real_estate.otp_max_attempts', DEFAULT_MAX_ATTEMPTS)),
            'resend_cooldown_seconds': int(self.icp.get_param('real_estate.otp_resend_cooldown_seconds', DEFAULT_RESEND_COOLDOWN_SECONDS)),
            'rate_limit_per_hour': int(self.icp.get_param('real_estate.otp_rate_limit_per_hour', DEFAULT_RATE_LIMIT_PER_HOUR)),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_and_send(self, phone: str, purpose: str, ip_address: str = None) -> dict:
        """Generates a new OTP, persists its hash, sends it via the
        active SMS provider. Enforces resend cooldown and hourly rate
        limit before doing any work.

        Returns: {'phone': phone, 'expires_in_seconds': int}
        Raises: OTPCooldownError, OTPRateLimitExceeded, OTPSendFailedError, ValidationError
        """
        self._validate_phone(phone)
        config = self._get_config()

        self._enforce_resend_cooldown(phone, purpose, config)
        self._enforce_rate_limit(phone, config)

        raw_code = self.otp_model.generate_raw_code(config['code_length'])
        code_hash = self.otp_model.hash_code(raw_code)
        expires_at = fields.Datetime.now() + timedelta(minutes=config['expiry_minutes'])

        provider = SMSProviderFactory.get_provider(self.env)
        send_result = provider.send_otp(phone, raw_code)

        if not send_result.get('success'):
            _logger.warning('OTP send failed for %s via %s: %s', phone, provider.name(), send_result.get('raw'))
            raise OTPSendFailedError()
        provider_name = provider.name().lower().replace("provider", "")

        if provider_name == "smsmisr":
            provider_name = "sms_misr"

        self.otp_model.sudo().create({
            'phone': phone,
            'purpose': purpose,
            'code_hash': code_hash,
            'expires_at': expires_at,
            'max_attempts': config['max_attempts'],
            'last_sent_at': fields.Datetime.now(),
            'provider': provider_name,
            'provider_message_id': send_result.get('provider_message_id'),
            'ip_address': ip_address,
        })

        return {
            'phone': phone,
            'expires_in_seconds': config['expiry_minutes'] * 60,
        }

    def verify(self, phone: str, code: str, purpose: str) -> bool:
        """Verifies `code` against the latest active OTP for phone+purpose.

        Raises: OTPExpiredError, OTPInvalidError, OTPMaxAttemptsExceeded
        Returns True on success (OTP is marked consumed — one-time use).
        """
        self._validate_phone(phone)
        if not code:
            raise ValidationError('Code is required.')

        otp = self.otp_model.sudo().find_active(phone, purpose)
        if not otp:
            # Distinguish "never existed / already consumed" from "expired"
            # for a clearer client-facing message where possible.
            latest = self.otp_model.sudo().find_latest(phone, purpose)
            if latest and latest.is_expired():
                raise OTPExpiredError()
            raise OTPInvalidError()

        if otp.attempts >= otp.max_attempts:
            raise OTPMaxAttemptsExceeded()

        if otp.code_hash != self.otp_model.hash_code(code):
            otp.register_failed_attempt()
            remaining = otp.max_attempts - otp.attempts
            if remaining <= 0:
                raise OTPMaxAttemptsExceeded()
            raise OTPInvalidError()

        otp.mark_consumed()
        return True

    def resend(self, phone: str, purpose: str, ip_address: str = None) -> dict:
        """Thin wrapper — cooldown/rate-limit checks are shared with
        generate_and_send so resend can't be used to bypass them.
        """
        return self.generate_and_send(phone, purpose, ip_address=ip_address)

    # ------------------------------------------------------------------
    # Internal guards
    # ------------------------------------------------------------------
    def _validate_phone(self, phone: str):
        if not phone or len(phone) < 8:
            raise ValidationError('A valid phone number is required.')

    def _enforce_resend_cooldown(self, phone, purpose, config):
        latest = self.otp_model.sudo().find_latest(phone, purpose)
        if not latest or not latest.last_sent_at:
            return
        elapsed = (fields.Datetime.now() - latest.last_sent_at).total_seconds()
        cooldown = config['resend_cooldown_seconds']
        if elapsed < cooldown:
            raise OTPCooldownError(seconds_remaining=int(cooldown - elapsed))

    def _enforce_rate_limit(self, phone, config):
        key = f'otp_rate_limit:{phone}'
        allowed = RateLimiter.hit(
            self.env, key,
            limit=config['rate_limit_per_hour'],
            window_seconds=3600,
        )
        if not allowed:
            raise OTPRateLimitExceeded()
