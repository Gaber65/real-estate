from odoo import models, fields

class ChangeStateWizard(models.TransientModel):
    _name = 'change.state.wizard'
    _description = 'Change State Wizard'

    reason = fields.Text()

    def action_confirm(self):
        active_id = self.env.context.get('active_id')
        record = self.env['property'].browse(active_id)

        record.state = 'closed'

        return {'type': 'ir.actions.act_window_close'}