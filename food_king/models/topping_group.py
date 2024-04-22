from odoo import models, api,fields
import requests
import json

class product_tooping_group_food_king(models.Model):
    _inherit = 'topping.groups'

    food_king_id = fields.Integer(string="Food king id", default=False)