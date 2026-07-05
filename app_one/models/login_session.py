# -*- coding: utf-8 -*-
from odoo import api, fields, models


class RealEstateLoginSession(models.Model):
    _name = 'real_estate.login_session'
    _description = 'Login Session (one per device)'
    _order = 'last_active_at desc'

    user_id = fields.Many2one('res.users', string='User', required=True, index=True, ondelete='cascade')
    device_id = fields.Char(string='Device ID', required=True, index=True)
    device_name = fields.Char(string='Device Name')

    ip_address = fields.Char(string='IP Address')
    user_agent = fields.Char(string='User Agent')

    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now)
    last_active_at = fields.Datetime(string='Last Active At', default=fields.Datetime.now)

    is_active = fields.Boolean(string='Active', default=True, index=True)
    logged_out_at = fields.Datetime(string='Logged Out At')

    def touch(self):
        self.write({'last_active_at': fields.Datetime.now()})

    def close(self):
        self.write({'is_active': False, 'logged_out_at': fields.Datetime.now()})

    @api.model
    def list_active_for_user(self, user_id):
        return self.sudo().search([('user_id', '=', user_id), ('is_active', '=', True)])
