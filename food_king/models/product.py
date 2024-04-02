from odoo import models, fields,api

class ProductFoodKing(models.Model):
    _inherit = 'product.template'

    food_king_id = fields.Integer(string="Food king id", default=False)
    item_type = fields.Selection([
        ('veg', 'Veg'),
        ('nonveg', 'Non-Veg')
    ], string="Item Type", default='veg')
    is_featured = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Is Featured", default='no')
    caution = fields.Text(string="Caution")
    description = fields.Text(string="Description")
    food_king_active = fields.Boolean(string="Food King Active", default=True)





       