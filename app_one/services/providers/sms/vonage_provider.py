# -*- coding: utf-8 -*-
import logging

import requests

from .base_sms_provider import BaseSMSProvider

_logger = logging.getLogger(__name__)


class VonageProvider(BaseSMSProvider):
    API_URL = 'https://rest.nexmo.com/sms/json'

    def send_otp(self, phone: str, code: str) -> dict:
        api_key = self.icp.get_param('real_estate.vonage_api_key')
        api_secret = self.icp.get_param('real_estate.vonage_api_secret')
        brand_name = self.icp.get_param('real_estate.vonage_brand_name', default='RealEstate')

        if not all([api_key, api_secret]):
            _logger.error('Vonage credentials are not configured.')
            return {'success': False, 'provider_message_id': None, 'raw': {'error': 'not_configured'}}

        payload = {
            'api_key': api_key,
            'api_secret': api_secret,
            'to': phone,
            'from': brand_name,
            'text': f'Your verification code is {code}. It expires in 5 minutes.',
        }

        try:
            response = requests.post(self.API_URL, data=payload, timeout=10)
            data = response.json()
            messages = data.get('messages', [{}])
            first = messages[0] if messages else {}
            success = first.get('status') == '0'
            if not success:
                _logger.warning('Vonage send failed: %s', first.get('error-text'))
            return {
                'success': success,
                'provider_message_id': first.get('message-id'),
                'raw': data,
            }
        except requests.RequestException as exc:
            _logger.exception('Vonage request error')
            return {'success': False, 'provider_message_id': None, 'raw': {'error': str(exc)}}
