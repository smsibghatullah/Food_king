from odoo import models, fields, api

class SuccessWizard(models.TransientModel):
    _name = 'food_king.success_wizard'
    _description = 'Success Wizard'

    message = fields.Text('Message', readonly=True)

    @api.model
    def show_message(self, message):
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'food_king.success_wizard',
            'target': 'new',
            'context': {'default_message': message}
        }
