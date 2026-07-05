"""
Deprecated compatibility shim for legacy JwtHelper usage.

This module used to contain a self-contained JWT implementation with a
hardcoded SECRET_KEY and bespoke payload fields. To remove duplicated
JWT logic and keep a single source of truth we now delegate to the
centralised TokenService (which reads the secret from
`ir.config_parameter` and implements blacklist/rotation logic).

The old helper methods are preserved as thin wrappers so existing code
that imports JwtHelper.* keeps working. New code should import and use
TokenService directly.
"""

from odoo.http import request
from uuid import uuid4

try:
    # Local import to avoid circular dependency during package import time.
    from ..services.auth.token_service import TokenService
except Exception:
    TokenService = None


class JwtHelper:
    @staticmethod
    def generate_access_token(user_id):
        """Delegate to TokenService.issue_access_token(user).

        Keeps the old single-argument signature but uses the canonical
        TokenService implementation under the hood.
        """
        if TokenService is None:
            raise RuntimeError('TokenService not available')
        user = request.env['res.users'].sudo().browse(user_id)
        return TokenService(request.env).issue_access_token(user)

    @staticmethod
    def generate_refresh_token(user_id, device_id=None, device_name=None, ip_address=None, user_agent=None):
        """Delegate to TokenService.issue_refresh_token.

        The legacy helper accepted only a user_id; TokenService requires a
        device_id. To remain compatible we generate a stable legacy
        device_id when none is provided to avoid raising errors for old
        callsites. New code should pass an explicit device_id.
        """
        if TokenService is None:
            raise RuntimeError('TokenService not available')
        if not device_id:
            device_id = f'legacy-{user_id}-{uuid4().hex}'
        user = request.env['res.users'].sudo().browse(user_id)
        return TokenService(request.env).issue_refresh_token(
            user, device_id=device_id, device_name=device_name, ip_address=ip_address, user_agent=user_agent,
        )

    @staticmethod
    def decode(token):
        """Delegate to TokenService.decode_and_verify and return the payload."""
        if TokenService is None:
            raise RuntimeError('TokenService not available')
        return TokenService(request.env).decode_and_verify(token)
