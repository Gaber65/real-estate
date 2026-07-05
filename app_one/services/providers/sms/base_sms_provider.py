# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class BaseSMSProvider(ABC):
    """Every concrete SMS provider must implement this interface.

    OTPService only ever talks to this contract — never to a concrete
    provider class directly — so providers can be swapped via a single
    ir.config_parameter change with zero changes to business logic.
    """

    def __init__(self, env):
        self.env = env
        self.icp = env['ir.config_parameter'].sudo()

    @abstractmethod
    def send_otp(self, phone: str, code: str) -> dict:
        """Send `code` to `phone`.

        Returns:
            {
                'success': bool,
                'provider_message_id': str | None,
                'raw': dict,   # raw provider response, for debugging/audit
            }
        Must NOT raise on provider-side failure — return success=False
        instead, so OTPService can decide how to surface the error
        (callers should never have to catch provider-specific exceptions).
        """
        raise NotImplementedError

    def name(self) -> str:
        return self.__class__.__name__
