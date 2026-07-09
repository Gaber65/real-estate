from odoo import models, fields


class PropertyBanner(models.Model):
    _name = 'property.banner'
    _description = 'Property Banner'

    name = fields.Char(required=True)
    image = fields.Image(string='Image', max_width=1024, max_height=1024)
    sequence = fields.Integer(default=10, index=True)
    active = fields.Boolean(default=True)
    start_date = fields.Date()
    end_date = fields.Date()
    property_id = fields.Many2one('property', string='Property')
    tag_id = fields.Many2one('tag', string='Tag')
    action_type = fields.Selection([
        ('none', 'None'),
        ('property', 'Property'),
        ('tag', 'Tag'),
        ('external_link', 'External Link')
    ], default='none')
    external_url = fields.Char()