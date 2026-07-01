import random

from ..utils.jwt_auth import JwtAuth
from ..utils.jwt_helper import JwtHelper
from odoo.http import request
from odoo.exceptions import ValidationError


class AuthService:

    @staticmethod
    def register(data):

        phone = data.get('phone')
        password = data.get('password')
        name = data.get('name')

        if not phone:
            raise ValidationError(
                'Phone is required'
            )

        if not password:
            raise ValidationError(
                'Password is required'
            )

        exists = request.env[
            'res.users'
        ].sudo().search(
            [('phone', '=', phone)],
            limit=1
        )

        if exists:
            raise ValidationError(
                'Phone already exists'
            )

        user = request.env[
            'res.users'
        ].sudo().create({
            'name': name,
            'login': phone,
            'phone': phone,
            'password': password,
            'user_type': 'customer',
        })

        customer_group = request.env.ref(
            'app_one.group_estate_customer'
        )

        user.write({
            'groups_id': [(4, customer_group.id)]
        })

        request.env[
            'estate.customer'
        ].sudo().create({
            'user_id': user.id,
            'full_name': name,
            'phone': phone,
        })

        return user

    @staticmethod
    def login(phone, password):

        user = request.env[
            'res.users'
        ].sudo().search(
            [('phone', '=', phone)],
            limit=1
        )

        if not user:
            raise ValidationError(
                "Invalid credentials"
            )

        try:
            user._check_credentials(
                password,
                {'interactive': False}
            )
        except Exception:
            raise ValidationError(
                "Invalid credentials"
            )

        access_token = (
            JwtHelper.generate_access_token(
                user.id
            )
        )

        refresh_token = (
            JwtHelper.generate_refresh_token(
                user.id
            )
        )

        request.env[
            'estate.auth.token'
        ].sudo().create({
            'user_id': user.id,
            'access_token': access_token,
            'refresh_token': refresh_token,
        })

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "phone": user.phone
            }
        }
    @staticmethod
    def send_otp(phone):

        if not phone:
            raise ValidationError(
                'Phone is required'
            )

        otp_code = str(
            random.randint(100000, 999999)
        )

        otp = request.env[
            'estate.otp'
        ].sudo().create({
            'phone': phone,
            'otp_code': otp_code,
        })

        return {
            'phone': otp.phone,
            'otp': otp.otp_code
        }
    @staticmethod
    def verify_otp(phone, otp_code):

        otp = request.env[
            'estate.otp'
        ].sudo().search([
            ('phone', '=', phone),
            ('otp_code', '=', otp_code),
            ('verified', '=', False)
        ], limit=1)

        if not otp:
            raise ValidationError(
                'Invalid OTP'
            )

        otp.verified = True

        user = request.env[
            'res.users'
        ].sudo().search([
            ('phone', '=', phone)
        ], limit=1)

        if user:
            user.is_verified = True

        return {
            'verified': True
        }

    @staticmethod
    def refresh_token(refresh_token):

        payload = JwtHelper.decode(
            refresh_token
        )

        if payload["type"] != "refresh":
            raise ValidationError(
                "Invalid refresh token"
            )

        access_token = (
            JwtHelper.generate_access_token(
                payload["user_id"]
            )
        )

        return {
            "access_token": access_token
        }

    @staticmethod
    def logout():

        auth_header = request.httprequest.headers.get(
            "Authorization"
        )

        token = auth_header.replace(
            "Bearer ",
            ""
        )

        token_record = request.env[
            'estate.auth.token'
        ].sudo().search(
            [('access_token', '=', token)],
            limit=1
        )

        if token_record:
            token_record.write({
                'revoked': True
            })

        return True

    @staticmethod
    def get_profile():

        user = JwtAuth.current_user()

        return {
            "id": user.id,
            "name": user.name,
            "phone": user.phone,
            "verified": user.is_verified
        }