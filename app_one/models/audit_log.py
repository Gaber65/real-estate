# -*- coding: utf-8 -*-
from odoo import fields, models


class RealEstateAuditLog(models.Model):
    _name = 'real_estate.audit_log'
    _description = 'Audit Log'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='User', index=True)
    action = fields.Selection(
        selection=[
            ('login', 'Login'),
            ('login_failed', 'Login Failed'),
            ('logout', 'Logout'),
            ('logout_all', 'Logout All Devices'),
            ('register', 'Register'),
            ('password_change', 'Password Change'),
            ('property_create', 'Property Created'),
            ('property_update', 'Property Updated'),
            ('property_delete', 'Property Deleted'),
            ('property_approve', 'Property Approved'),
            ('property_reject', 'Property Rejected'),
            ('favorite_add', 'Favorite Added'),
            ('favorite_remove', 'Favorite Removed'),
        ],
        string='Action', required=True, index=True,
    )
    model_name = fields.Char(string='Model')
    record_id = fields.Integer(string='Record ID')
    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string='User Agent')
    metadata_json = fields.Text(string='Metadata (JSON)')
