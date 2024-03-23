from odoo import models, api,fields

class account_tax_food_king(models.Model):
    _inherit = 'account.tax'

    food_king_id = fields.Integer(string="Food king id")











       