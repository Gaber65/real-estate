# -*- coding: utf-8 -*-
import logging

from odoo import fields

from ...helpers.exceptions import (
    ValidationError,
    ConflictError,
    InvalidCredentialsError,
    AccountLockedError,
)
from ...helpers.rate_limiter import RateLimiter
from .otp_service import OTPService
from .token_service import TokenService
from ..audit_log_service import AuditLogService

_logger = logging.getLogger(__name__)

DEFAULT_LOGIN_MAX_ATTEMPTS = 5
DEFAULT_LOGIN_LOCKOUT_MINUTES = 15
DEFAULT_LOGIN_RATE_LIMIT_PER_15MIN = 10


class AuthService:
    """Orchestrates register/login/logout/password flows. Delegates
    OTP handling to OTPService and token issuance/rotation to
    TokenService — this class never touches a token or an OTP row
    directly, it only calls those services.
    """

    def __init__(self, env):
        self.env = env
        self.user_model = env['res.users']
        self.icp = env['ir.config_parameter'].sudo()
        self.otp_service = OTPService(env)
        self.token_service = TokenService(env)
        self.audit_log_service = AuditLogService(env)

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------
    def register(self, phone, password, name, email=None, ip_address=None):
        if not phone or not password or not name:
            raise ValidationError('phone, password and name are required.')
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters.')

        existing = self.user_model.sudo().search(['|', ('phone', '=', phone), ('login', '=', email or phone)], limit=1)
        if existing:
            raise ConflictError('An account with this phone or email already exists.')

        user = self.user_model.sudo().create({
            'name': name,
            'login': email or phone,
            'email': email,
            'phone': phone,
            'phone_verified': False,
            'is_active_account': False,   # activated once OTP is verified
            'active': True,               # Odoo-level active — keep True so search works; gate with is_active_account instead
            'role_key': 'customer',
        })
        user.set_api_password(password)

        self.otp_service.generate_and_send(phone, purpose='register', ip_address=ip_address)
        self._log('register', user_id=user.id, ip=ip_address)

        return {'user_id': user.id, 'phone': user.phone}

    def verify_registration_otp(self, phone, code):
        self.otp_service.verify(phone, code, purpose='register')
        user = self.user_model.find_by_phone_or_email(phone)
        if not user:
            raise ValidationError('No pending registration found for this phone.')
        user.sudo().write({'phone_verified': True, 'is_active_account': True})
        return {'user_id': user.id}

    # ------------------------------------------------------------------
    # Login / Logout
    # ------------------------------------------------------------------
    def login(self, identifier, password, device_id, device_name=None, ip_address=None, user_agent=None):
        if not identifier or not password or not device_id:
            raise ValidationError('identifier, password and device_id are required.')

        self._enforce_login_rate_limit(identifier, ip_address)

        user = self.user_model.find_by_phone_or_email(identifier)
        if not user:
            # Same error/timing profile as "wrong password" — never reveal
            # whether the account exists.
            raise InvalidCredentialsError()

        if user.is_locked():
            raise AccountLockedError()

        if not user.is_active_account:
            raise InvalidCredentialsError('Account is not active. Please verify your phone number first.')

        if not user.verify_api_password(password):
            user.register_failed_login(
                max_attempts=int(self.icp.get_param('real_estate.login_max_attempts', DEFAULT_LOGIN_MAX_ATTEMPTS)),
                lockout_minutes=int(self.icp.get_param('real_estate.login_lockout_minutes', DEFAULT_LOGIN_LOCKOUT_MINUTES)),
            )
            self._log('login_failed', user_id=user.id, ip=ip_address)
            raise InvalidCredentialsError()

        user.reset_failed_logins()

        access_token = self.token_service.issue_access_token(user)
        refresh_token = self.token_service.issue_refresh_token(
            user, device_id=device_id, device_name=device_name, ip_address=ip_address, user_agent=user_agent,
        )
        self._log('login', user_id=user.id, ip=ip_address)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {'id': user.id, 'name': user.name, 'phone': user.phone, 'role': user.role_key},
        }

    def logout(self, access_token, refresh_token):
        if refresh_token:
            self.token_service.revoke(refresh_token)
        if access_token:
            self.token_service.blacklist_access_token(access_token)

    def logout_all_devices(self, user_id):
        self.token_service.revoke_all_for_user(user_id)
        self._log('logout_all', user_id=user_id)

    # ------------------------------------------------------------------
    # Forgot / Reset / Change password
    # ------------------------------------------------------------------
    def forgot_password(self, phone, ip_address=None):
        # Always behave the same whether or not the phone exists, to
        # avoid leaking account existence via response timing/shape.
        user = self.user_model.find_by_phone_or_email(phone)
        if user:
            self.otp_service.generate_and_send(phone, purpose='reset_password', ip_address=ip_address)
        return {'message': 'If this phone is registered, a verification code has been sent.'}

    def reset_password(self, phone, code, new_password):
        if not new_password or len(new_password) < 8:
            raise ValidationError('Password must be at least 8 characters.')

        self.otp_service.verify(phone, code, purpose='reset_password')

        user = self.user_model.find_by_phone_or_email(phone)
        if not user:
            raise ValidationError('Account not found.')

        user.set_api_password(new_password)
        user.reset_failed_logins()
        self.token_service.revoke_all_for_user(user.id)  # force re-login everywhere after a reset
        self._log('password_change', user_id=user.id)
        return {'message': 'Password reset successfully. Please log in again.'}

    def change_password(self, user_id, old_password, new_password):
        if not new_password or len(new_password) < 8:
            raise ValidationError('New password must be at least 8 characters.')

        user = self.user_model.sudo().browse(user_id)
        if not user.exists():
            raise ValidationError('User not found.')
        if not user.verify_api_password(old_password):
            raise InvalidCredentialsError('Current password is incorrect.')

        user.set_api_password(new_password)
        self._log('password_change', user_id=user.id)
        return {'message': 'Password changed successfully.'}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _enforce_login_rate_limit(self, identifier, ip_address):
        key = f'login_rate_limit:{ip_address or identifier}'
        allowed = RateLimiter.hit(
            self.env, key,
            limit=int(self.icp.get_param('real_estate.login_rate_limit_per_15min', DEFAULT_LOGIN_RATE_LIMIT_PER_15MIN)),
            window_seconds=900,
        )
        if not allowed:
            raise InvalidCredentialsError('Too many login attempts. Please try again later.')

    def _log(self, action, user_id=None, ip=None):
        try:
            self.audit_log_service.log(action=action, user_id=user_id)
        except Exception:
            # Audit logging must never break the auth flow itself.
            _logger.exception('Failed to write audit log for action=%s', action)
