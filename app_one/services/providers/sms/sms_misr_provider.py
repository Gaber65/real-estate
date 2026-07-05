# -*- coding: utf-8 -*-

import logging
import requests

from .base_sms_provider import BaseSMSProvider

_logger = logging.getLogger(__name__)


class SMSMisrProvider(BaseSMSProvider):
    """
    SMSMisr OTP API Provider

    Documentation:
    https://smsmisr.com/api/OTP/
    """

    API_URL = "https://smsmisr.com/api/OTP/"

    def send_otp(self, phone: str, code: str) -> dict:
        """Send OTP using SMSMisr OTP API"""

        username = self.icp.get_param("real_estate.sms_misr_username")
        password = self.icp.get_param("real_estate.sms_misr_password")
        sender = self.icp.get_param("real_estate.sms_misr_sender")
        template = self.icp.get_param("real_estate.sms_misr_template")

        if not username:
            return self._error("Missing SMSMisr Username")

        if not password:
            return self._error("Missing SMSMisr Password")

        if not sender:
            return self._error("Missing SMSMisr Sender")

        if not template:
            return self._error("Missing SMSMisr Template")

        mobile = self._normalize_phone(phone)

        payload = {
            "environment": 2,  # 2 = Test, 1 = Live
            "username": username,
            "password": password,
            "sender": sender,
            "mobile": mobile,
            "template": template,
            "otp": str(code),
        }

        _logger.info("========== SMSMisr OTP ==========")
        _logger.info("URL: %s", self.API_URL)
        _logger.info("Payload: %s", {
            "environment": payload["environment"],
            "username": username,
            "sender": sender,
            "mobile": mobile,
            "template": template,
            "otp": code,
        })

        try:
            response = requests.post(
                self.API_URL,
                data=payload,
                timeout=20,
            )

            _logger.info("HTTP Status: %s", response.status_code)
            _logger.info("Response Body: %s", response.text)

            try:
                data = response.json()
            except Exception:
                data = {"raw": response.text}

            # SMSMisr sometimes returns "Code" and sometimes "code"
            api_code = str(
                data.get("Code") or
                data.get("code") or
                ""
            )

            success = (
                    response.status_code == 200 and
                    api_code == "4901"
            )

            _logger.info("SMSMisr API Code: %s", api_code)
            _logger.info("SMSMisr Success: %s", success)

            return {
                "success": success,
                "provider_message_id": data.get("SMSID"),
                "raw": data,
            }

        except requests.Timeout:
            _logger.exception("SMSMisr timeout")

            return self._error("Connection timeout")

        except requests.ConnectionError:
            _logger.exception("SMSMisr connection error")

            return self._error("Connection error")

        except Exception as e:
            _logger.exception("SMSMisr unexpected error")

            return self._error(str(e))

    @staticmethod
    def _normalize_phone(phone):
        """
        Convert

        01012345678
        +201012345678
        201012345678

        to

        201012345678
        """

        phone = phone.strip()

        if phone.startswith("+20"):
            return phone[1:]

        if phone.startswith("20"):
            return phone

        if phone.startswith("0"):
            return "20" + phone[1:]

        return phone

    @staticmethod
    def _error(message):
        return {
            "success": False,
            "provider_message_id": None,
            "raw": {
                "error": message
            }
        }
