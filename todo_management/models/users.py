from odoo import models, fields

class Users(models.Model):
    _inherit = 'res.users'

    task_ids = fields.One2many(
        'todo.task',
        'assignTo',
        string='Tasks'
    )