from odoo import models, fields

class Tag(models.Model):
    _name = 'tag'
    _description = 'Tag'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10, index=True)
    active = fields.Boolean(default=True)
    image = fields.Image(string='Image', max_width=256, max_height=256)
    property_ids = fields.Many2many('property', string='Properties')
