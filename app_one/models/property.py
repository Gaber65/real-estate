from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class Property(models.Model):
    _name = 'property'
    _description = 'Property for Real Estate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(required=True, help="Enter property name", translate=True)
    description = fields.Text()

    postcode = fields.Char(required=True, tracking=True)
    date_availability = fields.Date(required=True)

    tag_ids = fields.Many2many('tag')

    expected_price = fields.Float(required=True)
    active = fields.Boolean(default=True)

    selling_price = fields.Float(
        compute='_compute_selling_price',
        store=True
    )
    profit_percentage = fields.Float(default=25.0)

    building_id = fields.Many2one('building')
    bedrooms = fields.Integer()
    living_area = fields.Integer()
    facades = fields.Integer()

    garage = fields.Boolean()
    garden = fields.Boolean()
    garden_area = fields.Integer()

    # Owner relationships (BOTH options)
    owner_id = fields.Many2one('owner', string="Owner Profile")
    owner_user_id = fields.Many2one(
        'res.users',
        string="Owner User",
        domain="[('user_type', '=', 'owner')]",
        help="Direct link to owner user account"
    )

    # Agent relationship
    agent_user_id = fields.Many2one(
        'res.users',
        string="Agent",
        domain="[('user_type', '=', 'agent')]",
        help="Agent managing this property"
    )

    # Customer who purchased
    customer_user_id = fields.Many2one(
        'res.users',
        string="Customer",
        domain="[('user_type', '=', 'customer')]",
        help="Customer who purchased this property"
    )

    # Related fields for display
    owner_address = fields.Char(related='owner_id.address', readonly=False)
    owner_phone = fields.Char(related='owner_id.phone', readonly=False)
    owner_email = fields.Char(related='owner_id.email', readonly=False)
    owner_name = fields.Char(related='owner_id.name', string="Owner Name")

    # Images
    property_image_ids = fields.One2many(
        'property.image',
        'property_id',
        string="Images",
        copy=True
    )
    image_1920 = fields.Image(
        string="Cover Image",
        max_width=1920,
        max_height=1920
    )

    # Property lines
    property_line_ids = fields.One2many('property.line', 'property_id')

    garden_orientation = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West')
    ])

    # Constraints
    _sql_constraints = [
        ('post_code_unique', 'unique(postcode)', 'Postcode must be unique'),
        ('expected_price_positive', 'CHECK(expected_price > 0)', 'Expected price must be positive')
    ]

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('sold', 'Sold'),
        ('closed', 'Closed')
    ], default='draft', tracking=True)

    expected_selling_date = fields.Date()
    is_late = fields.Boolean(compute="_compute_is_late", store=True)
    sequence = fields.Char(default='new', readonly=True)

    # Computes
    @api.depends('expected_price', 'profit_percentage')
    def _compute_selling_price(self):
        for rec in self:
            rec.selling_price = rec.expected_price * (1 + rec.profit_percentage / 100)

    @api.depends('expected_selling_date', 'state')
    def _compute_is_late(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_late = bool(
                rec.expected_selling_date
                and rec.expected_selling_date < today
                and rec.state not in ['sold', 'closed']
            )

    # Constraints
    @api.constrains('expected_price')
    def _check_expected_price(self):
        for rec in self:
            if rec.expected_price <= 0:
                raise ValidationError("Expected price must be greater than zero.")

    @api.constrains('owner_id', 'owner_user_id')
    def _check_owner_consistency(self):
        for rec in self:
            if rec.owner_id and rec.owner_user_id and rec.owner_id.user_id != rec.owner_user_id:
                raise ValidationError("Owner profile and owner user must match.")

    # State actions
    def action_draft(self):
        self.write({'state': 'draft'})

    def action_pending(self):
        self.write({'state': 'pending'})

    def action_sold(self):
        for rec in self:
            if rec.state == 'closed':
                raise UserError("Cannot sell a closed property.")
        self.write({'state': 'sold'})

    def action_closed(self):
        self.write({'state': 'closed'})

    def action_open_change_state_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'change.state.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_property_id': self.id},
        }

    def open_owner_action_form_btn(self):
        if not self.owner_id:
            raise UserError("This property has no owner assigned.")
        action = self.env['ir.actions.actions']._for_xml_id('app_one.owner_action')
        view_id = self.env.ref('app_one.owner_view_form').id
        action['res_id'] = self.owner_id.id
        action['views'] = [[view_id, 'form']]
        return action

    # CRUD overrides
    @api.model
    def create(self, vals):
        # Auto-create owner if owner_user_id is provided but no owner_id
        if vals.get('owner_user_id') and not vals.get('owner_id'):
            user = self.env['res.users'].browse(vals.get('owner_user_id'))
            if user.user_type == 'owner':
                owner = self.env['owner'].search([('user_id', '=', user.id)], limit=1)
                if owner:
                    vals['owner_id'] = owner.id
                else:
                    # Auto-create owner profile
                    owner = self.env['owner'].create({
                        'name': user.name,
                        'email': user.email,
                        'phone': user.phone,
                        'user_id': user.id,
                    })
                    vals['owner_id'] = owner.id

        record = super().create(vals)
        record.sequence = self.env['ir.sequence'].next_by_code('property_sequence')
        return record

    def write(self, vals):
        # Prevent modification of closed properties
        for rec in self:
            if rec.state == 'closed':
                raise ValidationError("Closed properties cannot be modified.")

        # Sync owner_id if owner_user_id changed
        if vals.get('owner_user_id') and not vals.get('owner_id'):
            user = self.env['res.users'].browse(vals.get('owner_user_id'))
            if user.user_type == 'owner':
                owner = self.env['owner'].search([('user_id', '=', user.id)], limit=1)
                if owner:
                    vals['owner_id'] = owner.id

        return super().write(vals)

    # Additional methods
    def action_send_email(self):
        """Send property details via email"""
        template = self.env.ref('app_one.email_template_property_details')
        if template:
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)

    def action_duplicate(self):
        """Duplicate property with new sequence"""
        new_property = self.copy()
        return new_property


class PropertyLine(models.Model):
    _name = 'property.line'
    _description = 'Property Line'

    property_id = fields.Many2one('property', ondelete='cascade')
    description = fields.Char(required=True)
    area = fields.Float(required=True)
    sequence = fields.Integer(default=10)