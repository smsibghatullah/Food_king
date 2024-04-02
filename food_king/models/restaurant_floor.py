from odoo import models, api,fields

class restaurant_floor_food_king(models.Model):
    _inherit = 'restaurant.floor'

    food_king_id = fields.Integer(string="Food king id", default=False)











       