# -*- coding: utf-8 -*-
import logging

import requests

from .base_sms_provider import BaseSMSProvider

_logger = logging.getLogger(__name__)


class TwilioProvider(BaseSMSProvider):
    """Sends a plain SMS containing our own OTP code via Twilio's
    Programmable Messaging API.

    Note: this deliberately does NOT use Twilio Verify's own OTP
    lifecycle (generation/expiry/attempts), because OTPService owns
    that lifecycle so the same logic works identically regardless of
    which provider is active. Twilio here is a pure "send this SMS"
    transport.
    """

    API_BASE = 'https://api.twilio.com/2010-04-01'

    def send_otp(self, phone: str, code: str) -> dict:
        account_sid = self.icp.get_param('real_estate.twilio_account_sid')
        auth_token = self.icp.get_param('real_estate.twilio_auth_token')
        from_number = self.icp.get_param('real_estate.twilio_from_number')

        if not all([account_sid, auth_token, from_number]):
            _logger.error('Twilio credentials are not configured.')
            return {'success': False, 'provider_message_id': None, 'raw': {'error': 'not_configured'}}

        url = f'{self.API_BASE}/Accounts/{account_sid}/Messages.json'
        body = f'Your verification code is {code}. It expires in 5 minutes.'

        try:
            response = requests.post(
                url,
                data={'From': from_number, 'To': phone, 'Body': body},
                auth=(account_sid, auth_token),
                timeout=10,
            )
            data = response.json()
            success = response.status_code in (200, 201)
            if not success:
                _logger.warning('Twilio send failed: %s', data.get('message'))
            return {
                'success': success,
                'provider_message_id': data.get('sid'),
                'raw': data,
            }
        except requests.RequestException as exc:
            _logger.exception('Twilio request error')
            return {'success': False, 'provider_message_id': None, 'raw': {'error': str(exc)}}
