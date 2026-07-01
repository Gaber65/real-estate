# models/estate_auth_token.py

from odoo import models, fields


class EstateAuthToken(models.Model):
    _name = 'estate.auth.token'
    _description = 'Authentication Tokens'

    user_id = fields.Many2one(
        'res.users',
        required=True,
        ondelete='cascade'
    )

    access_token = fields.Text(
        required=True
    )

    refresh_token = fields.Text(
        required=True
    )

    expires_at = fields.Datetime()

    revoked = fields.Boolean(
        default=False
    )