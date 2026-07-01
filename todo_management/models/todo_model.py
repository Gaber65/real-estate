from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TodoTask(models.Model):
    _name = 'todo.task'
    _description = 'To Do Task'

    name = fields.Char(string='Task', required=True)
    assignTo = fields.Many2one(
        'res.users',
        string='Assign To'
    )
    description = fields.Text(string='Description')
    dueDate = fields.Date(string='Due Date')

    status = fields.Selection(
        [
            ('new', 'New'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
        ],
        string='Status',
        default='new',
        tracking=True,
    )

    active = fields.Boolean(default=True)

    task_line_ids = fields.One2many(
        'todo.task.line.estimation',
        'task_id',
        string='Task Lines'
    )

    total_time = fields.Float(
        string='Total Time',
        help='Total time in hours'
    )

    is_late = fields.Boolean(
        string='Is Late',
        compute='_compute_is_late',
        store=True
    )

    @api.depends('status', 'dueDate')
    def _compute_is_late(self):
        today = fields.Date.today()

        for task in self:
            task.is_late = (
                task.status != 'done'
                and task.dueDate
                and task.dueDate < today
            )

    def write(self, vals):
        if vals.get('status') == 'done':
            for rec in self:
                if rec.total_time <= 0:
                    raise ValidationError(
                        'Please set Total Time before moving task to Done.'
                    )

        return super().write(vals)

    def action_mark_as_done(self):
        self.write({'status': 'done'})

    def action_mark_as_new(self):
        self.write({'status': 'new'})

    def action_mark_as_in_progress(self):
        self.write({'status': 'in_progress'})


class TaskLinesEstimation(models.Model):
    _name = 'todo.task.line.estimation'
    _description = 'Todo Task Line Estimation'

    task_id = fields.Many2one(
        'todo.task',
        string='Task',
        ondelete='cascade'
    )

    owner_id = fields.Many2one(
        'res.users',
        string='Owner'
    )

    time = fields.Float(
        string='Time (Hours)',
        required=True
    )

    @api.constrains('time')
    def _check_total_time(self):
        for record in self:
            if record.task_id and record.task_id.total_time:

                total_line_time = sum(
                    record.task_id.task_line_ids.mapped('time')
                )

                if total_line_time > record.task_id.total_time:
                    raise ValidationError(
                        f'Total line hours ({total_line_time}) '
                        f'cannot exceed task total time '
                        f'({record.task_id.total_time}).'
                    )