from odoo import http
from odoo.http import request

from ..utils.global_response import GlobalResponse
from ..utils.api_exception_handler import api_exception_handler
from ..utils.jwt_auth import JwtAuth

from ..services.auth_service import AuthService

import json


class AuthController(http.Controller):

    @http.route(
        '/api/auth/register',
        methods=['POST'],
        type='http',
        auth='public',
        csrf=False
    )
    @api_exception_handler
    def register(self):

        data = json.loads(
            request.httprequest.data.decode('utf-8')
        )

        user = AuthService.register(data)

        return GlobalResponse.api_response(
            success=True,
            message='Account created successfully',
            data=user,
            status=201
        )

    @http.route(
        '/api/auth/login',
        methods=['POST'],
        type='http',
        auth='public',
        csrf=False
    )
    @api_exception_handler
    def login(self):

        data = json.loads(
            request.httprequest.data.decode('utf-8')
        )

        result = AuthService.login(
            phone=data.get('phone'),
            password=data.get('password')
        )

        return GlobalResponse.api_response(
            success=True,
            message='Login successful',
            data=result,
            status=200
        )

    @http.route(
        '/api/auth/send-otp',
        methods=['POST'],
        type='http',
        auth='public',
        csrf=False
    )
    @api_exception_handler
    def send_otp(self):

        data = json.loads(
            request.httprequest.data.decode('utf-8')
        )

        result = AuthService.send_otp(
            data.get('phone')
        )

        return GlobalResponse.api_response(
            success=True,
            message='OTP sent successfully',
            data=result,
            status=200
        )

    @http.route(
        '/api/auth/verify-otp',
        methods=['POST'],
        type='http',
        auth='public',
        csrf=False
    )
    @api_exception_handler
    def verify_otp(self):

        data = json.loads(
            request.httprequest.data.decode('utf-8')
        )

        result = AuthService.verify_otp(
            phone=data.get('phone'),
            otp_code=data.get('otp')
        )

        return GlobalResponse.api_response(
            success=True,
            message='OTP verified successfully',
            data=result,
            status=200
        )

    @http.route(
        '/api/auth/refresh-token',
        methods=['POST'],
        type='http',
        auth='public',
        csrf=False
    )
    @api_exception_handler
    def refresh_token(self):

        data = json.loads(
            request.httprequest.data.decode('utf-8')
        )

        result = AuthService.refresh_token(
            data.get('refresh_token')
        )

        return GlobalResponse.api_response(
            success=True,
            message='Token refreshed successfully',
            data=result,
            status=200
        )

    @http.route(
        '/api/auth/logout',
        methods=['POST'],
        type='http',
        auth='public',
        csrf=False
    )
    @api_exception_handler
    def logout(self):

        JwtAuth.current_user()

        AuthService.logout()

        return GlobalResponse.api_response(
            success=True,
            message='Logged out successfully',
            status=200
        )

    @http.route(
        '/api/profile',
        methods=['GET'],
        type='http',
        auth='public',
        csrf=False
    )
    @api_exception_handler
    def get_profile(self):

        JwtAuth.current_user()

        profile = AuthService.get_profile()

        return GlobalResponse.api_response(
            success=True,
            message='Profile retrieved successfully',
            data=profile,
            status=200
        )