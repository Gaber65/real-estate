# -*- coding: utf-8 -*-
from .vonage_provider import VonageProvider
from .sms_misr_provider import SMSMisrProvider


class ProviderNotConfiguredError(Exception):
    def __init__(self, provider_name):
        super().__init__(f'SMS provider "{provider_name}" is not registered or not configured.')
        self.provider_name = provider_name


class SMSProviderFactory:
    """Registry + factory. Adding a fourth provider later only means:
    1. write a class implementing BaseSMSProvider
    2. register it below
    No changes anywhere in OTPService or the controllers.
    """

    _providers = {
        'vonage': VonageProvider,
        'sms_misr': SMSMisrProvider,
    }

    @classmethod
    def register(cls, name, provider_cls):
        cls._providers[name] = provider_cls

    @classmethod
    def get_provider(cls, env):
        icp = env['ir.config_parameter'].sudo()
        active_name = icp.get_param('real_estate.sms_provider', default='sms_misr')
        provider_cls = cls._providers.get(active_name)
        if not provider_cls:
            raise ProviderNotConfiguredError(active_name)
        return provider_cls(env)
