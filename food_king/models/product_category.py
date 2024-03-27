from odoo import models, api,fields

class product_category_food_king(models.Model):
    _inherit = 'pos.category'

    food_king_id = fields.Integer(string="Food king id")
    description = fields.Text(string="Description")
 











       