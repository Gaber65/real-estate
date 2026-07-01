from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EstateCustomer(models.Model):
    _name = 'estate.customer'
    _description = 'Estate Customer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    user_id = fields.Many2one(
        'res.users',
        required=True,
        ondelete='cascade',
        string="User Account"
    )

    # Fields from user (computed)
    full_name = fields.Char(related='user_id.full_name', string="Full Name", store=True)
    phone = fields.Char(related='user_id.phone', string="Phone", store=True)
    email = fields.Char(related='user_id.email', string="Email", store=True)
    address = fields.Char(related='user_id.address', string="Address", store=True)
    image = fields.Image(related='user_id.profile_image', string="Image", store=True)
    is_verified = fields.Boolean(related='user_id.is_verified', string="Verified")

    # Customer specific fields
    preferred_contact = fields.Selection([
        ('phone', 'Phone'),
        ('email', 'Email'),
        ('whatsapp', 'WhatsApp')
    ], default='phone', string="Preferred Contact Method")

    notes = fields.Text(string="Notes")
    date_joined = fields.Date(default=fields.Date.today)

    # Property interests
    interested_property_ids = fields.Many2many(
        'property',
        string="Interested Properties"
    )

    # Purchased properties
    purchased_property_ids = fields.One2many(
        'property',
        'customer_user_id',
        string="Purchased Properties"
    )

    # Search and preferences
    min_price = fields.Float(string="Min Budget")
    max_price = fields.Float(string="Max Budget")
    preferred_area = fields.Char(string="Preferred Area")

    @api.constrains('user_id')
    def _check_user_type(self):
        for customer in self:
            if customer.user_id.user_type != 'customer':
                raise ValidationError("Customer profile must be linked to a Customer user.")

    def action_view_interested_properties(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Interested Properties',
            'res_model': 'property',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.interested_property_ids.ids)],
        }

    def action_view_purchased_properties(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchased Properties',
            'res_model': 'property',
            'view_mode': 'tree,form',
            'domain': [('customer_user_id', '=', self.user_id.id)],
        }

    def action_open_user(self):
        """Open the linked user account"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'User Account',
            'res_model': 'res.users',
            'view_mode': 'form',
            'res_id': self.user_id.id,
            'target': 'current',
        }