from odoo import models, fields,api
import requests

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

    def update_product(self):
        food_king = self.env['food_king.food_king'].sudo().search([], limit=1)
        if not food_king:
             print('Food King settings not configured. Please configure Food King settings first.')

        headers = {
            'Authorization': f'Bearer {food_king.auth_token}',
            'X-Api-Key': food_king.license_key or '',
        }

        payload = {
            "id":self.food_king_id,
            "name": self.name,
            "price": self.list_price,
            "item_category_id": self.pos_categ_ids[0].food_king_id,
            "tax_id": self.taxes_id[0].food_king_id if self.taxes_id else None,
            "item_type":  5 if self.item_type == 'veg' else 10,
            "is_featured": 10  if self.is_featured == 'no' else 5,
            "description": self.description or '',
            "caution": self.caution or '',
            "order": self.sequence,
            "status": 5 if self.food_king_active else 10 ,
            }
        
        url_get_id = f"{food_king.url}/api/admin/item/{self.food_king_id}"
        response_get_id = requests.post(url_get_id, headers=headers, data=payload)
        pos_data = response_get_id.json()
        print(pos_data,"ggggggggggggggg")
        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        dic_msg = "Product Update Successfully"
        context['message'] = dic_msg
        return{
                'name': 'Success',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'sh.message.wizard',
                'views':[(view.id,'form')],
                'view_id':view.id,
                'target': 'new',
                'context': context,
        }





       