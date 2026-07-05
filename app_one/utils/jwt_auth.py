from odoo.http import request
from odoo.exceptions import ValidationError

from ..services.auth.token_service import TokenService


class JwtAuth:
    @staticmethod
    def current_user():
        auth_header = request.httprequest.headers.get('Authorization')
        if not auth_header:
            raise ValidationError('Authorization header missing')
        if not auth_header.startswith('Bearer '):
            raise ValidationError('Invalid authorization header')
        token = auth_header.replace('Bearer ', '', 1).strip()

        payload = TokenService(request.env).decode_and_verify(token)
        # TokenService uses 'sub' as the subject (user id)
        user_id = payload.get('sub')
        if not user_id:
            raise ValidationError('Token payload missing subject')
        return request.env['res.users'].sudo().browse(user_id)
