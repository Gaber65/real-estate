from odoo import models, fields


class PropertyImage(models.Model):
    _name = 'property.image'
    _description = 'Property Image'
    _order = 'sequence, id'

    sequence = fields.Integer(
        default=10,
        help="Order of the image (lower numbers appear first)"
    )
    name = fields.Char(
        string="Name",
        help="Optional name/description for the image"
    )
    image_1920 = fields.Image(
        string="Image",
        max_width=1920,
        max_height=1920,
        required=True
    )
    property_id = fields.Many2one(
        'property',
        string="Property",
        ondelete='cascade',
        index=True,
        required=True
    )