# -*- coding: utf-8 -*-
import hashlib
import secrets

from odoo import api, fields, models


class RealEstateRefreshToken(models.Model):
    _name = 'real_estate.refresh_token'
    _description = 'Refresh Token'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='User', required=True, index=True, ondelete='cascade')
    token_hash = fields.Char(string='Token Hash', required=True, index=True)

    device_id = fields.Char(string='Device ID', required=True, index=True)
    device_name = fields.Char(string='Device Name')

    session_id = fields.Many2one('real_estate.login_session', string='Session', ondelete='cascade')

    issued_at = fields.Datetime(string='Issued At', default=fields.Datetime.now)
    expires_at = fields.Datetime(string='Expires At', required=True, index=True)
    revoked_at = fields.Datetime(string='Revoked At')

    replaced_by_token_id = fields.Many2one('real_estate.refresh_token', string='Replaced By')

    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string='User Agent')

    _sql_constraints = [
        ('token_hash_unique', 'unique(token_hash)', 'Duplicate refresh token hash.'),
    ]

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()

    @staticmethod
    def generate_raw_token() -> str:
        return secrets.token_urlsafe(48)

    def is_expired(self) -> bool:
        self.ensure_one()
        return self.expires_at < fields.Datetime.now()

    def is_revoked(self) -> bool:
        self.ensure_one()
        return bool(self.revoked_at)

    def is_active(self) -> bool:
        return not self.is_expired() and not self.is_revoked()

    def revoke(self):
        self.write({'revoked_at': fields.Datetime.now()})

    @api.model
    def find_by_raw_token(self, raw_token):
        return self.sudo().search([('token_hash', '=', self.hash_token(raw_token))], limit=1)

    def revoke_family(self):
        """Walk the replaced_by_token_id chain in both directions and
        revoke every token descended from / ancestor to this one — used
        when token reuse (theft) is detected, per rotation-reuse defense.
        """
        self.ensure_one()
        seen = self.browse()
        # Walk forward (children)
        current = self
        while current and current not in seen:
            seen |= current
            current.revoke()
            current = current.replaced_by_token_id
        # Walk backward (parents) in case reuse happened on an older token
        parent = self.sudo().search([('replaced_by_token_id', '=', self.id)], limit=1)
        while parent and parent not in seen:
            seen |= parent
            parent.revoke()
            parent = self.sudo().search([('replaced_by_token_id', '=', parent.id)], limit=1)

    @api.model
    def cleanup_expired(self, days_old=30):
        from datetime import timedelta
        cutoff = fields.Datetime.now() - timedelta(days=days_old)
        stale = self.sudo().search([('expires_at', '<', cutoff)])
        count = len(stale)
        stale.unlink()
        return count
