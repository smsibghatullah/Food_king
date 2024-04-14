from odoo import models, fields

class YourBranchModel(models.Model):
    _name = 'food.king.branch'
    _description = 'Branch'

    name = fields.Char(string='Name')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    latitude = fields.Float(string='Latitude')
    longitude = fields.Float(string='Longitude')
    city = fields.Char(string='City')
    state = fields.Char(string='State')
    zip_code = fields.Char(string='Zip Code')
    status = fields.Integer(string='Status')
    food_king_id = fields.Integer(string='Food King ID')


