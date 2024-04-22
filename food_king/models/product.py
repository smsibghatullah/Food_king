from odoo import models, fields,api
import requests
import base64
import tempfile
import os
import json

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
    food_king_id_topping = fields.Integer(string="Food king Topping id", default=False)
    food_king_id_variant = fields.Integer(string="Food king Variation id", default=False)
    

    def update_product(self):
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

            if self.attribute_line_ids:
                    urlgetattri =f"{food_king.url}/api/admin/item/variation/group-by-attribute/{self.food_king_id}?id={self.food_king_id}&paginate=0&order_column=id&order_type=asc"
                    response_attribute_get = requests.get(urlgetattri, headers=headers,data={})
                    response_data_attribute_get = response_attribute_get.json()
                    print(response_data_attribute_get['data'],"====================+++++++++++++++++++++++++++++++++++++++++++++++")
                    attribute_get_data = [item['item_attribute_id'] for item in response_data_attribute_get['data']]
                    attribute_children_id = []
                    synced_artibutes =self.env['product.attribute'].search([('product_tmpl_ids', '=', self.id)])
                    for artibutes in synced_artibutes:
                            if artibutes.food_king_id in attribute_get_data:
                                url_atribute =f"{food_king.url}/api/admin/setting/item-attribute/{artibutes.food_king_id}"
                                
                                payload_atribute = json.dumps({
                                    "name": artibutes.name,
                                    "status": 5 if artibutes.food_king_active else 10
                                })

                                response_atribute = requests.put(url_atribute, headers=headers_topping, data=payload_atribute)
                                response_data_atribute = response_atribute.json()

                            else:
                                synced_artibutes = self.env['product.attribute'].search([('food_king_id', '=', 0)])
                                url_atribute =f"{food_king.url}/api/admin/setting/item-attribute"
                                
                                synced_artibutes_ids = []
                                for artibutes in synced_artibutes:
                                        payload_atribute = {
                                            "name": artibutes.name,
                                            "status": 5 if artibutes.food_king_active else 10
                                        }
                                        try:
                                            response_atribute = requests.post(url_atribute, headers=headers, data=payload_atribute)
                                            response_data_atribute = response_atribute.json()
                                            if 'data' in response_data_atribute:
                                                food_king_id_atribute = response_data_atribute['data']['id']
                                                artibutes.write({'food_king_id': food_king_id_atribute})
                                                synced_artibutes_ids.append(artibutes.id)

                                        except requests.exceptions.RequestException as e:
                                            return {'error': str(e)}




                                for item_data in response_data_attribute_get['data']:
                                        attribute_children_id = [item['id'] for item in item_data['children']]
                                        print(self.valid_product_template_attribute_line_ids,"================================================================>")
                                        artibuteline=self.env['product.template.attribute.value'].search([])
                                        for attribute_line in self.attribute_line_ids:
                                                for value_id in attribute_line.value_ids:
                                                        for line_ids_price in artibuteline:
                                                            if line_ids_price.food_king_id in attribute_children_id:
                                                                print(line_ids_price.attribute_id.id == attribute_line.attribute_id.id and line_ids_price.name == value_id.name,"ttttttttttttttttttttttttttttttttttt")
                                                                if line_ids_price.attribute_id.id == attribute_line.attribute_id.id and line_ids_price.name == value_id.name:
                                                                    print(line_ids_price.price_extra,line_ids_price.name,"kkkkkkkkkkkllllllllllllllllllvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
                                                                    payload_atribute2  = json.dumps({
                                                                        "name": line_ids_price.name,
                                                                        "price": line_ids_price.price_extra,
                                                                        "item_attribute_id": attribute_line.attribute_id.food_king_id,
                                                                        "caution":  attribute_line.attribute_id.caution if  attribute_line.attribute_id.caution else '',
                                                                        "status": 5 if attribute_line.attribute_id.food_king_active else 10
                                                                    })
                                                                    url_get_id_atribute2  = f"{food_king.url}/api/admin/item/variation/{self.food_king_id}/{line_ids_price.food_king_id}"
                                                                    response_get_id_atribute2  = requests.request("Put", url_get_id_atribute2 , headers=headers_topping , data=payload_atribute2 )
                                                                    response_data_atribute2  = response_get_id_atribute2 .json()
                                                        
                                                            else:   
                                                                        artibutes = self.env['product.attribute'].search([])
                                                                        artibuteline=self.env['product.template.attribute.value'].search([])
                                                                        for attribute_line in self.attribute_line_ids:
                                                                            for value_id in attribute_line.value_ids:
                                                                                    for line_ids_price in artibuteline:
                                                                                        if line_ids_price.attribute_id.id == attribute_line.attribute_id.id and line_ids_price.name == value_id.name:
                                                                                            payload_atribute2  = {
                                                                                                "name": line_ids_price.name,
                                                                                                "price": line_ids_price.price_extra,
                                                                                                "item_attribute_id": attribute_line.attribute_id.food_king_id,
                                                                                                "caution": attribute_line.attribute_id.caution,
                                                                                                "status": 5 if attribute_line.attribute_id.food_king_active else 10
                                                                                            }
                                                                                            url_get_id_atribute2  =f"{food_king.url}/api/admin/item/variation/{self.food_king_id}"
                                                                                            response_get_id_atribute2  = requests.request("POST", url_get_id_atribute2 , headers=headers , data=payload_atribute2 )
                                                                                            response_data_atribute2  = response_get_id_atribute2 .json()
                                                                                            if 'data' in response_data_atribute2 :
                                                                                                food_king_id_atribute2  = response_data_atribute2 ['data']['id']
                                                                                                value_id.write({'food_king_id': food_king_id_atribute2 })
                                                                                                line_ids_price.write({'food_king_id': food_king_id_atribute2 })
                                                                                                self.write({'food_king_id_variant':food_king_id_atribute2})

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
        

   