# -*- coding: utf-8 -*-
from odoo import api, fields, models


class RealEstateTokenBlacklist(models.Model):
    """Tiny table: one row per explicitly-logged-out access token,
    kept only until its natural expiry (cron sweeps it after that,
    since an expired JWT is rejected on 'exp' anyway)."""
    _name = 'real_estate.token_blacklist'
    _description = 'Access Token Blacklist'

    jti = fields.Char(string='JWT ID', required=True, index=True)
    expires_at = fields.Datetime(string='Expires At', required=True, index=True)

    _sql_constraints = [
        ('jti_unique', 'unique(jti)', 'Token already blacklisted.'),
    ]

    @api.model
    def cleanup_expired(self):
        stale = self.sudo().search([('expires_at', '<', fields.Datetime.now())])
        count = len(stale)
        stale.unlink()
        return count
