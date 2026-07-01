from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    phone = fields.Char(string="Phone")
    is_verified = fields.Boolean(default=False, string="Phone Verified")

    user_type = fields.Selection([
        ('admin', 'Admin'),
        ('agent', 'Agent'),
        ('customer', 'Customer'),
        ('owner', 'Owner')
    ], default='customer', required=True)

    # Profile fields
    profile_image = fields.Image(max_width=200, max_height=200)
    address = fields.Char(string="Address")
    full_name = fields.Char(compute='_compute_full_name', store=True)

    # Relationships
    owner_id = fields.One2many('owner', 'user_id', string="Owner Profile")
    customer_id = fields.One2many('estate.customer', 'user_id', string="Customer Profile")

    # Property relationships
    owned_property_ids = fields.One2many(
        'property',
        'owner_user_id',
        string="Properties Owned"
    )

    managed_property_ids = fields.One2many(
        'property',
        'agent_user_id',
        string="Managed Properties"
    )

    purchased_property_ids = fields.One2many(
        'property',
        'customer_user_id',
        string="Purchased Properties"
    )

    @api.depends('name', 'partner_id.name')
    def _compute_full_name(self):
        for user in self:
            user.full_name = user.name or user.partner_id.name or ''

    @api.constrains('user_type')
    def _check_user_type(self):
        for user in self:
            if user.user_type == 'admin' and not user.has_group('app_one.group_estate_admin'):
                raise ValidationError("Admin users must have the Estate Admin group.")

    @api.model
    def _get_security_group_xmlids(self, user_type):
        """Get the appropriate security group xmlids for a given user type"""
        group_map = {
            'admin': [
                'app_one.group_estate_admin',
                'app_one.group_estate_user',
                'base.group_system',  # Full system access
                'base.group_no_one',  # Technical features
            ],
            'agent': [
                'app_one.group_estate_agent',
                'app_one.group_estate_user',
            ],
            'customer': [
                'app_one.group_estate_customer',
                'app_one.group_estate_user',
            ],
            'owner': [
                'app_one.group_estate_owner',
                'app_one.group_estate_user',
            ],
        }
        return group_map.get(user_type, ['app_one.group_estate_customer'])

    def get_security_groups(self):
        """Get the appropriate security groups based on user type"""
        self.ensure_one()
        return self._get_security_group_xmlids(self.user_type)

    @api.model
    def _get_group_ids_for_type(self, user_type):
        """Resolve group xmlids to actual group ids, skipping any that don't exist yet"""
        group_ids = []
        for group_xml_id in self._get_security_group_xmlids(user_type):
            group = self.env.ref(group_xml_id, raise_if_not_found=False)
            if group:
                group_ids.append(group.id)
        return group_ids

    @api.model
    def create(self, vals):
        # Ensure the correct groups are part of vals BEFORE creation, since
        # @api.constrains checks (like _check_user_type) run inside
        # super().create() itself -- assigning groups afterwards is too late.
        if vals.get('user_type'):
            group_ids = self._get_group_ids_for_type(vals['user_type'])
            if group_ids:
                vals = dict(vals)
                vals['groups_id'] = vals.get('groups_id', []) + [(4, gid) for gid in group_ids]
        return super().create(vals)

    def write(self, vals):
        """Override write to handle user_type changes"""
        if vals.get('user_type'):
            group_ids = self._get_group_ids_for_type(vals['user_type'])
            if group_ids:
                vals = dict(vals)
                vals['groups_id'] = vals.get('groups_id', []) + [(4, gid) for gid in group_ids]
        return super().write(vals)

    def action_make_admin(self):
        """Make selected users admins"""
        for user in self:
            # Get admin groups
            admin_group = self.env.ref('base.group_system')
            estate_admin_group = self.env.ref('app_one.group_estate_admin')
            estate_user_group = self.env.ref('app_one.group_estate_user')

            # Add user to admin groups
            user.write({
                'groups_id': [
                    (4, admin_group.id),
                    (4, estate_admin_group.id),
                    (4, estate_user_group.id)
                ],
                'user_type': 'admin'
            })

    def action_make_agent(self):
        """Make selected users agents"""
        for user in self:
            agent_group = self.env.ref('app_one.group_estate_agent')
            user_group = self.env.ref('app_one.group_estate_user')
            user.write({
                'groups_id': [
                    (4, agent_group.id),
                    (4, user_group.id)
                ],
                'user_type': 'agent'
            })

    def action_make_customer(self):
        """Make selected users customers"""
        for user in self:
            customer_group = self.env.ref('app_one.group_estate_customer')
            user_group = self.env.ref('app_one.group_estate_user')
            user.write({
                'groups_id': [
                    (4, customer_group.id),
                    (4, user_group.id)
                ],
                'user_type': 'customer'
            })

    def action_make_owner(self):
        """Make selected users owners"""
        for user in self:
            owner_group = self.env.ref('app_one.group_estate_owner')
            user_group = self.env.ref('app_one.group_estate_user')
            user.write({
                'groups_id': [
                    (4, owner_group.id),
                    (4, user_group.id)
                ],
                'user_type': 'owner'
            })