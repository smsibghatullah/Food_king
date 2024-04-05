from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

  
    branch_id = fields.Many2one('food.king.branch', string='Branch')
    
