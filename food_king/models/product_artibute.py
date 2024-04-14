from odoo import models, api,fields
import requests
import json

class product_atribute_food_king(models.Model):
    _inherit = 'product.attribute'

    food_king_id = fields.Integer(string="Food king id", default=False)
    food_king_active = fields.Boolean(string="Food King Active", default=True)
    caution = fields.Text(string="Caution")


     











       