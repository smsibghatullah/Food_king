from odoo import models, api,fields

class product_category_food_king(models.Model):
    _inherit = 'pos.session'

    pos_name_session = fields.Text(string="pos name")
 











       