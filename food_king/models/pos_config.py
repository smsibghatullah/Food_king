from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    show_accepted_orders = fields.Boolean(string="Show Accepted Orders")
