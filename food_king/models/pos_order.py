from odoo import models, api, fields
import requests

class pos_order_food_king(models.Model):
    _inherit = 'pos.order'

    food_king_id = fields.Integer(string="Food king id")
    status = fields.Char('Order Status')
    is_accepted = fields.Boolean("Is Accepted",default=False)

    def accept_order(self):
        search_pos = self.env['pos.config'].search([('name', '=', 'Food King Pos')]).mapped('id')
        
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
        response_get_id = requests.post(url_get_id, headers=headers, data=payload)
        pos_data = response_get_id.json()
        self.is_accepted = True


from odoo.exceptions import UserError

class CustomPosMakePayment(models.TransientModel):
    _inherit = "pos.make.payment"
    def check(self):
        res = super(CustomPosMakePayment, self).check()
        if res:
            order = self.env["pos.order"].browse(self.env.context.get("active_id"))
            order.accept_order()

        return res


        
