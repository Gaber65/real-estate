from odoo.http import request
from odoo.exceptions import ValidationError

from .jwt_helper import JwtHelper


class JwtAuth:

    @staticmethod
    def current_user():

        auth_header = request.httprequest.headers.get(
            "Authorization"
        )

        if not auth_header:
            raise ValidationError(
                "Authorization header missing"
            )

        if not auth_header.startswith(
            "Bearer "
        ):
            raise ValidationError(
                "Invalid authorization header"
            )

        token = auth_header.replace(
            "Bearer ",
            ""
        )

        payload = JwtHelper.decode(token)

        return request.env[
            'res.users'
        ].sudo().browse(
            payload["user_id"]
        )