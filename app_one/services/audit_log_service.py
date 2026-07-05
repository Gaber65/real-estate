# -*- coding: utf-8 -*-
import json
import logging

from odoo.http import request

_logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {'password', 'token', 'otp', 'code', 'refresh_token', 'access_token'}


class AuditLogService:
    """Plain service (not a model) — instantiate with `env` and call
    `.log(...)` from inside other services at the point of state
    change. Never call this from controllers directly; if a controller
    needs to log something no service already covers, that's a sign
    the logic belongs in a service instead.
    """

    def __init__(self, env):
        self.env = env

    def log(self, action, user_id=None, model_name=None, record_id=None, metadata=None):
        ip_address, user_agent = self._extract_request_context()
        self.env['real_estate.audit_log'].sudo().create({
            'user_id': user_id,
            'action': action,
            'model_name': model_name,
            'record_id': record_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'metadata_json': json.dumps(self._sanitize(metadata or {})),
        })

    @staticmethod
    def _sanitize(metadata: dict) -> dict:
        return {k: ('***' if k.lower() in SENSITIVE_KEYS else v) for k, v in metadata.items()}

    @staticmethod
    def _extract_request_context():
        try:
            return request.httprequest.remote_addr, request.httprequest.user_agent.string
        except Exception:
            return None, None
