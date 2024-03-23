from odoo import models, api,fields

class res_partner_food_king(models.Model):
    _inherit = 'res.partner'

    food_king_id_res = fields.Integer(string="Food king id")











       