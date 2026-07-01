from odoo import models, fields, api


class Building(models.Model):
    _name = 'building'
    _description = 'building for Real Estate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    name = fields.Char(help="Enter building name (max 4 characters)")
    description = fields.Text()
    code = fields.Char(tracking=1)
    active = fields.Boolean(default=True)
    property_ids = fields.One2many('property', 'building_id')