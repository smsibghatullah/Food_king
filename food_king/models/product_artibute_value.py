from odoo import models, api,fields
import requests
import json

class product_atribute_value_food_king(models.Model):
    _inherit = 'product.attribute.value'

    food_king_id = fields.Integer(string="Food king id", default=False)


     











       