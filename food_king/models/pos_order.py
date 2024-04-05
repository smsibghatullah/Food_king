from odoo import models, api, fields
import requests

class pos_order_food_king(models.Model):
    _inherit = 'pos.order'

    food_king_id = fields.Integer(string="Food king id")
    status = fields.Char('Order Status')

    def accept_order(self):
        # search_kitchen = self.env['pos_preparation_display.display'].search([('name', '=', 'Food King Kitchen')]).mapped('id')
        search_pos = self.env['pos.config'].search([('name', '=', 'Food King Pos')]).mapped('id')
        # if search_kitchen:
        #     print("already exist")
        # else : 
        #     vals = {
        #         'name': 'Food King Kitchen',
        #         'company_id': self.env.company.id,
        #         'pos_config_ids': search_pos,
                
        #     }
        #     self.env['pos_preparation_display.display'].create(vals)
        food_king = self.env['food_king.food_king'].sudo().search([], limit=1)
        if not food_king:
             print('Food King settings not configured. Please configure Food King settings first.')

        headers = {
            'Authorization': f'Bearer {food_king.auth_token}',
            'X-Api-Key': food_king.license_key or '',
        }

        payload = {
            "id":self.food_king_id,
            "status":7
            }

        url_get_id = f"{food_king.url}/api/admin/table-order/change-status/{self.food_king_id}"
        print(url_get_id,"kkkkkkkkkkkkkkkkkkkkkkkk")
        response_get_id = requests.post(url_get_id, headers=headers, data=payload)
        pos_data = response_get_id.json()
        # if pos_data:
        #     self.state = 'draft'
        print(pos_data,"ggggggggggggggg")

        
