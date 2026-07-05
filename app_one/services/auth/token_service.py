# -*- coding: utf-8 -*-
import logging
import time
import uuid

from odoo import fields
from datetime import timedelta

try:
    import jwt
except ImportError:
    jwt = None

from ...helpers.exceptions import (
    TokenExpiredError,
    TokenRevokedError,
    TokenReuseDetectedError,
    ValidationError,
)

_logger = logging.getLogger(__name__)

DEFAULT_ACCESS_TOKEN_TTL_MINUTES = 24 * 60  # 1440 minutes
DEFAULT_REFRESH_TOKEN_TTL_DAYS = 7


class TokenService:
    """Owns JWT access tokens (short-lived, self-contained) and opaque
    refresh tokens (long-lived, stored hashed, revocable, rotated on
    every use). Access tokens are never stored — they're stateless by
    design; only their jti is checked against the blacklist table so
    logout can invalidate one before natural expiry.
    """

    def __init__(self, env):
        self.env = env
        self.icp = env['ir.config_parameter'].sudo()
        self.refresh_token_model = env['real_estate.refresh_token']
        self.session_model = env['real_estate.login_session']
        self.blacklist_model = env['real_estate.token_blacklist']

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------
    def _secret(self):
        secret = self.icp.get_param('real_estate.jwt_secret')
        if not secret:
            raise RuntimeError(
                'real_estate.jwt_secret is not configured. Set it via '
                'ir.config_parameter (a long random value, not committed to source).'
            )
        return secret

    def _access_ttl_minutes(self):
        return int(self.icp.get_param('real_estate.access_token_ttl_minutes', DEFAULT_ACCESS_TOKEN_TTL_MINUTES))

    def _refresh_ttl_days(self):
        return int(self.icp.get_param('real_estate.refresh_token_ttl_days', DEFAULT_REFRESH_TOKEN_TTL_DAYS))

    # ------------------------------------------------------------------
    # Access tokens (JWT)
    # ------------------------------------------------------------------
    def issue_access_token(self, user) -> str:
        if jwt is None:
            raise RuntimeError('PyJWT is not installed. Run: pip install PyJWT')

        now = int(time.time())

        payload = {
            'sub': str(user.id),  # MUST be string
            'role': user.role_key,
            'jti': str(uuid.uuid4()),
            'iat': now,
            'exp': now + self._access_ttl_minutes() * 60,
        }

        return jwt.encode(
            payload,
            self._secret(),
            algorithm='HS256'
        )

    def decode_and_verify(self, access_token: str) -> dict:
        if jwt is None:
            raise RuntimeError('PyJWT is not installed. Run: pip install PyJWT')

        try:
            payload = jwt.decode(
                access_token,
                self._secret(),
                algorithms=['HS256']
            )

        except jwt.ExpiredSignatureError:
            raise TokenExpiredError()

        except jwt.InvalidTokenError as e:
            raise TokenRevokedError(str(e))

        # Check blacklist
        if self.blacklist_model.sudo().search_count([
            ('jti', '=', payload.get('jti'))
        ]):
            raise TokenRevokedError('Token has been revoked.')

        # Convert sub back to integer
        payload['sub'] = int(payload['sub'])

        return payload

    def blacklist_access_token(self, access_token: str):
        """Best-effort immediate invalidation for logout — access
        tokens are short-lived (default 15 min) so this closes the gap
        between 'user clicked logout' and 'token would have expired
        anyway'."""
        try:
            payload = jwt.decode(access_token, self._secret(), algorithms=['HS256'], options={'verify_exp': False})
        except Exception:
            return
        expires_at = fields.Datetime.now() + timedelta(seconds=max(payload.get('exp', 0) - int(time.time()), 0))
        self.blacklist_model.sudo().create({'jti': payload.get('jti'), 'expires_at': expires_at})

    # ------------------------------------------------------------------
    # Refresh tokens
    # ------------------------------------------------------------------
    def issue_refresh_token(self, user, device_id, device_name=None, ip_address=None, user_agent=None) -> str:
        if not device_id:
            raise ValidationError('device_id is required.')

        session = self.session_model.sudo().search([
            ('user_id', '=', user.id), ('device_id', '=', device_id), ('is_active', '=', True),
        ], limit=1)
        if not session:
            session = self.session_model.sudo().create({
                'user_id': user.id,
                'device_id': device_id,
                'device_name': device_name,
                'ip_address': ip_address,
                'user_agent': user_agent,
            })
        else:
            session.touch()

        raw_token = self.refresh_token_model.generate_raw_token()
        self.refresh_token_model.sudo().create({
            'user_id': user.id,
            'token_hash': self.refresh_token_model.hash_token(raw_token),
            'device_id': device_id,
            'device_name': device_name,
            'session_id': session.id,
            'expires_at': fields.Datetime.now() + timedelta(days=self._refresh_ttl_days()),
            'ip_address': ip_address,
            'user_agent': user_agent,
        })
        return raw_token

    def rotate_refresh_token(self, raw_token: str, ip_address=None, user_agent=None) -> dict:
        """Validates the incoming refresh token, detects reuse of an
        already-rotated/revoked token (theft signal), and returns a
        fresh access+refresh pair.

        Returns: {'access_token': str, 'refresh_token': str, 'user_id': int}
        Raises: TokenExpiredError, TokenRevokedError, TokenReuseDetectedError
        """
        token_row = self.refresh_token_model.find_by_raw_token(raw_token)
        if not token_row:
            raise TokenRevokedError('Refresh token not recognized.')

        if token_row.is_revoked():
            # This exact token was already used/rotated once before —
            # someone is replaying an old token. Nuke the whole family.
            _logger.warning('Refresh token reuse detected for user %s, device %s', token_row.user_id.id, token_row.device_id)
            token_row.revoke_family()
            raise TokenReuseDetectedError()

        if token_row.is_expired():
            raise TokenExpiredError()

        user = token_row.user_id
        new_raw_token = self.refresh_token_model.generate_raw_token()
        new_row = self.refresh_token_model.sudo().create({
            'user_id': user.id,
            'token_hash': self.refresh_token_model.hash_token(new_raw_token),
            'device_id': token_row.device_id,
            'device_name': token_row.device_name,
            'session_id': token_row.session_id.id,
            'expires_at': fields.Datetime.now() + timedelta(days=self._refresh_ttl_days()),
            'ip_address': ip_address or token_row.ip_address,
            'user_agent': user_agent or token_row.user_agent,
        })
        token_row.write({'revoked_at': fields.Datetime.now(), 'replaced_by_token_id': new_row.id})
        if token_row.session_id:
            token_row.session_id.touch()

        return {
            'access_token': self.issue_access_token(user),
            'refresh_token': new_raw_token,
            'user_id': user.id,
        }

    def revoke(self, raw_token: str):
        token_row = self.refresh_token_model.find_by_raw_token(raw_token)
        if token_row and not token_row.is_revoked():
            token_row.revoke()
            if token_row.session_id:
                token_row.session_id.close()

    def revoke_all_for_user(self, user_id: int):
        tokens = self.refresh_token_model.sudo().search([('user_id', '=', user_id), ('revoked_at', '=', False)])
        tokens.write({'revoked_at': fields.Datetime.now()})
        sessions = self.session_model.list_active_for_user(user_id)
        sessions.write({'is_active': False, 'logged_out_at': fields.Datetime.now()})

    def revoke_session(self, session_id: int, requesting_user_id: int):
        """IDOR guard lives here: only the session's own owner may
        revoke it — enforced at the data layer, not just the caller's
        good behavior."""
        session = self.session_model.sudo().browse(session_id)
        if not session.exists() or session.user_id.id != requesting_user_id:
            raise ValidationError('Session not found.')
        tokens = self.refresh_token_model.sudo().search([('session_id', '=', session_id), ('revoked_at', '=', False)])
        tokens.write({'revoked_at': fields.Datetime.now()})
        session.close()
