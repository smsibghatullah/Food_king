from odoo import models, api,fields

class restaurant_table_food_king(models.Model):
    _inherit = 'restaurant.table'

    food_king_id = fields.Integer(string="Food king id", default=False)











       