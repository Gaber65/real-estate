# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

from ..helpers.exception_handler import handle_exceptions
from ..helpers.global_response import GlobalResponse
from ..helpers.exceptions import ValidationError
from ..helpers.auth_guard import require_auth
from ..helpers.http_utils import get_json_body
from ..services.auth.otp_service import OTPService
from ..services.auth.auth_service import AuthService
from ..services.auth.token_service import TokenService


class AuthController(http.Controller):
    """Thin controller: parse request -> call one service method ->
    return GlobalResponse. No business logic lives here.

    Uses type='http' (not type='json') so clients send and receive
    plain JSON, with no JSON-RPC envelope required — see
    helpers/http_utils.py for why.
    """

    # ------------------------------------------------------------------
    # OTP (standalone endpoints, also used internally by register/reset)
    # ------------------------------------------------------------------
    @http.route('/api/auth/send-otp', type='http', auth='public', methods=['POST'], csrf=False)
    @handle_exceptions
    def send_otp(self, **kwargs):
        payload = get_json_body(request)
        phone = payload.get('phone')
        purpose = payload.get('purpose')
        if not phone or not purpose:
            raise ValidationError('phone and purpose are required.')

        result = OTPService(request.env).generate_and_send(
            phone=phone, purpose=purpose, ip_address=request.httprequest.remote_addr,
        )
        return GlobalResponse.success(data=result, message='Verification code sent.')

    @http.route('/api/auth/resend-otp', type='http', auth='public', methods=['POST'], csrf=False)
    @handle_exceptions
    def resend_otp(self, **kwargs):
        payload = get_json_body(request)
        phone = payload.get('phone')
        purpose = payload.get('purpose')
        if not phone or not purpose:
            raise ValidationError('phone and purpose are required.')

        result = OTPService(request.env).resend(
            phone=phone, purpose=purpose, ip_address=request.httprequest.remote_addr,
        )
        return GlobalResponse.success(data=result, message='Verification code resent.')

    @http.route('/api/auth/verify-otp', type='http', auth='public', methods=['POST'], csrf=False)
    @handle_exceptions
    def verify_otp(self, **kwargs):
        payload = get_json_body(request)
        phone = payload.get('phone')
        code = payload.get('code')
        purpose = payload.get('purpose')
        if not phone or not code or not purpose:
            raise ValidationError('phone, code and purpose are required.')

        OTPService(request.env).verify(phone=phone, code=code, purpose=purpose)
        return GlobalResponse.success(message='Code verified successfully.')

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------
    @http.route('/api/auth/register', type='http', auth='public', methods=['POST'], csrf=False)
    @handle_exceptions
    def register(self, **kwargs):
        payload = get_json_body(request)
        result = AuthService(request.env).register(
            phone=payload.get('phone'),
            password=payload.get('password'),
            name=payload.get('name'),
            email=payload.get('email'),
            ip_address=request.httprequest.remote_addr,
        )
        return GlobalResponse.success(
            data=result,
            message='Registration successful. Please verify your phone with the code sent via SMS.',
            status=201,
        )

    @http.route('/api/auth/register/verify-otp', type='http', auth='public', methods=['POST'], csrf=False)
    @handle_exceptions
    def verify_registration(self, **kwargs):
        payload = get_json_body(request)
        phone = payload.get('phone')
        code = payload.get('code')
        if not phone or not code:
            raise ValidationError('phone and code are required.')

        result = AuthService(request.env).verify_registration_otp(phone, code)
        return GlobalResponse.success(data=result, message='Account activated. You can now log in.')

    # ------------------------------------------------------------------
    # Login / Logout / Refresh
    # ------------------------------------------------------------------
    @http.route('/api/auth/login', type='http', auth='public', methods=['POST'], csrf=False ,cors="*")
    @handle_exceptions
    def login(self, **kwargs):
        payload = get_json_body(request)
        result = AuthService(request.env).login(
            identifier=payload.get('identifier'),
            password=payload.get('password'),
            device_id=payload.get('device_id'),
            device_name=payload.get('device_name'),
            ip_address=request.httprequest.remote_addr,
            user_agent=request.httprequest.user_agent.string,
        )
        return GlobalResponse.success(data=result, message='Login successful.')

    @http.route('/api/auth/refresh-token', type='http', auth='public', methods=['POST'], csrf=False)
    @handle_exceptions
    def refresh_token(self, **kwargs):
        payload = get_json_body(request)
        refresh_token = payload.get('refresh_token')
        if not refresh_token:
            raise ValidationError('refresh_token is required.')

        result = TokenService(request.env).rotate_refresh_token(
            refresh_token,
            ip_address=request.httprequest.remote_addr,
            user_agent=request.httprequest.user_agent.string,
        )
        return GlobalResponse.success(data=result, message='Token refreshed.')

    @http.route('/api/auth/logout', type='http', auth='public', methods=['POST'], csrf=False)
    @handle_exceptions
    @require_auth
    def logout(self, **kwargs):
        payload = get_json_body(request)
        AuthService(request.env).logout(
            access_token=request.jwt_access_token,
            refresh_token=payload.get('refresh_token'),
        )
        return GlobalResponse.success(message='Logged out successfully.')

    @http.route('/api/auth/logout-all', type='http', auth='public', methods=['POST'], csrf=False)
    @handle_exceptions
    @require_auth
    def logout_all(self, **kwargs):
        AuthService(request.env).logout_all_devices(request.jwt_user_id)
        return GlobalResponse.success(message='Logged out from all devices.')

    # ------------------------------------------------------------------
    # Forgot / Reset / Change password
    # ------------------------------------------------------------------
    @http.route('/api/auth/forgot-password', type='http', auth='public', methods=['POST'], csrf=False)
    @handle_exceptions
    def forgot_password(self, **kwargs):
        payload = get_json_body(request)
        phone = payload.get('phone')
        if not phone:
            raise ValidationError('phone is required.')

        result = AuthService(request.env).forgot_password(phone, ip_address=request.httprequest.remote_addr)
        return GlobalResponse.success(data=result, message=result['message'])

    @http.route('/api/auth/reset-password', type='http', auth='public', methods=['POST'], csrf=False)
    @handle_exceptions
    def reset_password(self, **kwargs):
        payload = get_json_body(request)
        phone = payload.get('phone')
        code = payload.get('code')
        new_password = payload.get('new_password')
        if not phone or not code or not new_password:
            raise ValidationError('phone, code and new_password are required.')

        result = AuthService(request.env).reset_password(phone, code, new_password)
        return GlobalResponse.success(message=result['message'])

    @http.route('/api/auth/change-password', type='http', auth='public', methods=['POST'], csrf=False)
    @handle_exceptions
    @require_auth
    def change_password(self, **kwargs):


        payload = get_json_body(request)
        old_password = payload.get('old_password')
        new_password = payload.get('new_password')


        if not old_password or not new_password:


            raise ValidationError('old_password and new_password are required.')


        result = AuthService(request.env).change_password(request.jwt_user_id, old_password, new_password)
        return GlobalResponse.success(message=result['message'])
