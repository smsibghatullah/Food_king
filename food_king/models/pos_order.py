from odoo import models, api,fields

class pos_order_food_king(models.Model):
    _inherit = 'pos.order'

    food_king_id = fields.Integer(string="Food king id")











       