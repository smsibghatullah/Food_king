from odoo import models, fields,api

class ResCompany(models.Model):
    _inherit = 'res.company'

  
    branch_id = fields.Many2one('food.king.branch', string='Branch')


    @api.model
    def create(self, values):
        company = super(ResCompany, self).create(values)

        food_king_values = {
            'username': 'admin@example.com',
            'password': '123456',
            'url': 'http://localhost:8001',
            'license_key': 'b6d68vy2-m7g5-20r0-5275-h103w73453q120',
            'company_id': company.id,
        }

        self.env['food_king.food_king'].sudo().create(food_king_values)

        # pos_config_values = {
        #     'name': 'Food King Pos',
        #     'company_id': company.id,
        #     'payment_method_ids':None,
        #     'journal_id':None,
        #     'invoice_journal_id':None
        # }

        # pos_config = self.env['pos.config'].sudo().create(pos_config_values)

        # session_values = {
        #         'name': pos_config.name,  
        #         'config_id': pos_config.id,
        #         'start_at': fields.Datetime.to_string(fields.Datetime.now()),  
        #         'stop_at': fields.Datetime.to_string(fields.Datetime.now()),
        #         'company_id': company.id,
        #         'pos_name_session': pos_config.name
        #     }
        # self.env['pos.session'].sudo().create(session_values)

        return company