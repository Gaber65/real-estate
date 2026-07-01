from odoo import models


class Client(models.Model):
    _name = 'client'
    _description = 'Client'
    _inherit = 'owner'