from odoo import models, api, fields
import requests
from odoo.exceptions import UserError

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
        print(payload,pos_data,"pppppppppppppppppppppppppppppppppppppppppppppppppppppp")
        self.is_accepted = True

    @api.model
    def accept_online_order(self):
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

        url_get_id = f"{food_king.url}/api/admin/online-order/change-status/{self.food_king_id}"
        response_get_id = requests.post(url_get_id, headers=headers, data=payload)
        pos_data = response_get_id.json()
        self.is_accepted = True

    def _process_order(self, order, draft, existing_draft_order):
        res = super(pos_order_food_king, self)._process_order(order, draft, existing_draft_order)
        print(existing_draft_order, "ooooooooooo", draft, "dddddddddddddd", order, "wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww")
        if res and isinstance(existing_draft_order, pos_order_food_king):
            existing_draft_order.accept_order()
            existing_draft_order.accept_online_order()
        return res


class CustomPosMakePayment(models.TransientModel):
    _inherit = "pos.make.payment"

    def check(self):
        res = super(CustomPosMakePayment, self).check()
        if res:
            order = self.env["pos.order"].browse(self.env.context.get("active_id"))
            order.accept_order()
            order.accept_online_order()

        return res


        
