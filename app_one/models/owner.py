from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Owner(models.Model):
    _name = 'owner'
    _description = 'Owner'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, string="Owner Name", help="Enter Owner Name")
    address = fields.Char()
    phone = fields.Char()
    email = fields.Char()
    owner_image = fields.Image(max_width=200, max_height=200)

    # Link to user account
    user_id = fields.Many2one(
        'res.users',
        string="User Account",
        help="Link to user account for authentication",
        ondelete='set null'
    )

    # Properties owned
    property_ids = fields.One2many('property', 'owner_id', string="Properties")

    # Computed fields
    is_user = fields.Boolean(compute='_compute_is_user', store=True)
    user_type = fields.Selection(related='user_id.user_type', store=True)
    full_name = fields.Char(related='user_id.full_name', string="User Full Name")

    @api.depends('user_id')
    def _compute_is_user(self):
        for owner in self:
            owner.is_user = bool(owner.user_id)

    @api.constrains('email')
    def _check_email(self):
        for owner in self:
            if owner.email and '@' not in owner.email:
                raise ValidationError("Invalid email address.")

    @api.model
    def create(self, vals):
        # Auto-create user if email is provided and no user linked
        if not vals.get('user_id') and vals.get('email'):
            # Check if user already exists with this email
            existing_user = self.env['res.users'].search([
                ('email', '=', vals.get('email'))
            ], limit=1)

            if not existing_user:
                user_vals = {
                    'name': vals.get('name', 'Owner'),
                    'login': vals.get('email'),
                    'email': vals.get('email'),
                    'user_type': 'owner',
                    'phone': vals.get('phone', ''),
                }
                user = self.env['res.users'].create(user_vals)
                vals['user_id'] = user.id
            else:
                vals['user_id'] = existing_user.id

        owner = super().create(vals)

        return owner

    def write(self, vals):
        result = super().write(vals)

        # Update user if email changed
        if vals.get('email') and self.user_id:
            self.user_id.write({'email': vals.get('email'), 'login': vals.get('email')})

        return result

    def action_view_properties(self):
        """Action to view owner's properties"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Properties',
            'res_model': 'property',
            'view_mode': 'tree,form',
            'domain': [('owner_id', '=', self.id)],
            'context': {'default_owner_id': self.id},
        }

    def action_create_user(self):
        """Create user account for owner if not exists"""
        for owner in self:
            if not owner.user_id:
                user_vals = {
                    'name': owner.name,
                    'login': owner.email or f"owner_{owner.id}@temp.com",
                    'email': owner.email or f"owner_{owner.id}@temp.com",
                    'phone': owner.phone or '',
                    'user_type': 'owner',
                }
                user = self.env['res.users'].create(user_vals)
                owner.write({'user_id': user.id})