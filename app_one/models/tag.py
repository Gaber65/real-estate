from odoo import models, fields


class Tag(models.Model):
    _name = 'tag'
    _description = 'Tag'

    name = fields.Char(required=True)

    property_ids = fields.Many2many('property')
