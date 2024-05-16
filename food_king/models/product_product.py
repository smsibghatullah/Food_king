from odoo import models, fields,api
import requests
import base64
import tempfile
import os
import json

class Product_product_FoodKing(models.Model):
    _inherit = 'product.product'

    is_update = fields.Boolean(string="Is Update" , required=False)

    def update_product_product(self):
            print("dddddddddddddddddddddddddddddddddddd")
            food_king = self.env['food_king.food_king'].sudo().search([], limit=1)
            if not food_king:
                print('Food King settings not configured. Please configure Food King settings first.')

            headers = {
                'Authorization': f'Bearer {food_king.auth_token}',
                'X-Api-Key': food_king.license_key or '',
            }

            image_base64 = ""
            image_data = base64.b64decode(self.image_1920) if self.image_1920 else ''
            files=[]
            if self.image_1920:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_file.write(image_data)
                    temp_file_path = temp_file.name

                files = [('image', ('Foodking.png', open(temp_file_path, 'rb'), 'image/png'))]

            payload = {
                "id":self.food_king_id,
                "name": self.name,
                "price": self.list_price,
                "item_category_id": self.pos_categ_ids[0].food_king_id,
                "tax_id": self.taxes_id[0].food_king_id if self.taxes_id else None,
                "item_type":  5 if self.item_type == 'veg' else 10,
                "is_featured": 10 if self.is_featured == 'no' else 5,
                "description": self.description or '',
                "caution": self.caution or '',
                "order": self.sequence,
                "status": 5 if self.food_king_active else 10 ,
            }
            print(payload)
            url_get_id = f"{food_king.url}/api/admin/item/{self.food_king_id}"
            response_get_id = requests.request("POST", url_get_id, headers=headers, data=payload, files=files)
            pos_data = response_get_id.json()
            headers_topping = {
                            'Authorization': f'Bearer {food_king.auth_token}',
                            'X-Api-Key': food_king.license_key or '',
                            'Content-Type': 'application/json',
                        }
            print(self.topping_ids,"aaaaaaaaaaaaaaaaaaaaaaaaaa")
            synced_topping = self.topping_ids
            Error_Message = []
            for topping in synced_topping:
                        if topping.food_king_id_topping != 0:
                            payload_topping = json.dumps({
                                "name": topping.name,
                                "price": topping.list_price,
                                "status": 5
                            })
                            print(payload_topping,"qqqqqqqqqqqqqqqqqqqqqqq")
                            try:
                                url = f"{food_king.url}/api/admin/item/extra/{self.food_king_id}/{topping.food_king_id_topping}"
                                response_topping = requests.put(url, headers=headers_topping, data=payload_topping)
                                response_data_topping = response_topping.json()
                                print(response_data_topping,"pppppppppppppppppppp")
                                    
                            except requests.exceptions.RequestException as e:
                                print( str(e))
                                pass
                        else:
                                    
                                    for topping in synced_topping:
                                            payload_topping = {
                                                "name": topping.name,
                                                "price": 0 if  topping.list_price == 0.0 else topping.list_price  ,
                                                "status": 5
                                            }
                                            print(payload_topping,"mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
                                            try:
                                                url = f"{food_king.url}/api/admin/item/extra/{self.food_king_id}"
                                                response_topping = requests.post(url, headers=headers, data=payload_topping)
                                                response_data_topping = response_topping.json()
                                                if 'message' in response_data_topping:
                                                    Error_Message.append("The Following Products is not sync there are some issues")
                                                    Error_Message.append('('+topping.name+')' + ' ' + response_data_topping['message'])
                                                print(response_data_topping,"bbbbbbbbbbbbbbbbbbbbbbb")
                                                    
                                                if 'data' in response_data_topping:
                                                    food_king_id_topping = response_data_topping['data']['id']
                                                    self.write({'food_king_id_topping': food_king_id_topping})
                                                    topping.write({'food_king_id_topping': food_king_id_topping})
                                            except requests.exceptions.RequestException as e:
                                                print( str(e))
                                                pass

         
                   
            view = self.env.ref('sh_message.sh_message_wizard')
            context = dict(self._context or {})
            dic_msg = "Product Update Successfully"+ os.linesep + '\n'.join(Error_Message)
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