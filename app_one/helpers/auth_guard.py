# -*- coding: utf-8 -*-
from functools import wraps

from odoo.http import request

from .exceptions import InvalidCredentialsError


def require_auth(func):
    """Validates the Authorization: Bearer <access_token> header via
    TokenService, and sets request.jwt_user_id before calling the
    wrapped controller method. Use on every route that needs an
    authenticated caller (anything under /api/me/*, change-password,
    logout, etc.).

    Deliberately does NOT set request.env.user / uid — this API is
    JWT-based and independent of Odoo's own session/web-login, so
    services receive the user id explicitly instead of relying on
    ambient Odoo session state.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):


        auth_header = request.httprequest.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            raise InvalidCredentialsError('Missing or malformed Authorization header.')
        access_token = auth_header[len('Bearer '):].strip()

        # Local import avoids a circular import between helpers and services.
        from ..services.auth.token_service import TokenService
        token_service = TokenService(request.env)
        payload = token_service.decode_and_verify(access_token)

        request.jwt_user_id = payload['sub']
        request.jwt_role = payload.get('role')
        request.jwt_access_token = access_token
        return func(self, *args, **kwargs)
    return wrapper
