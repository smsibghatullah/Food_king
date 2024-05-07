import requests
from odoo import models, fields, api,_
import json
from odoo.exceptions import AccessError,UserError
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
import re
import base64
import tempfile
import os
from playsound import playsound


class food_king(models.Model):
    _name = 'food_king.food_king'

    username = fields.Char('Username')
    password = fields.Char('Password', widget='password')
    url = fields.Char('URL')
    auth_token = fields.Char('Token')
    license_key = fields.Char('License Key')
    company_id = fields.Many2one('res.company', string='Company')
    point_of_sale = fields.Many2one('pos.config', string='Point Of Sale')
    company_branch_name = fields.Char(related="company_id.branch_id.name",string="Branch Name")

   #  get base64 

    def get_base64_from_url(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            base64_image = base64.b64encode(response.content).decode('utf-8')
            return base64_image
        except requests.exceptions.RequestException as e:
            return None
  
   #  get token  

    def get_token(self):
        Foodking_Ids = self.env['food_king.food_king'].search([('id', '=', 1)])
        login_url = (self.url or Foodking_Ids.url) + "/api/auth/login"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': '',
            'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
        }
        print(self.username)
        login_payload = {
            "email": self.username,
            "password": self.password
        }

        try:
            response = requests.post(login_url, headers=headers, json=login_payload)
            response_data = response.json()
            print(response_data,"ssssssssssssssssssssssssss")
            token = response_data['token']
            if not token:
                    view = self.env.ref('sh_message.sh_message_wizard')
                    context = dict(self._context or {})
                    dic_msg = "Failed to obtain access token."
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
            self.auth_token = token
            view = self.env.ref('sh_message.sh_message_wizard')
            context = dict(self._context or {})
            dic_msg = response_data.get('message', "Login Successfully")
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
            return token
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
  
   #  sync product

    def sync_all_products(self, cron_mode=True):
        Foodking_Ids_data = self.env['food_king.food_king'].sudo().search([])
        for Foodking_Ids  in Foodking_Ids_data :
            synced_products = self.env['product.template'].search([('food_king_id', '=', 0)])
            url = (self.url or Foodking_Ids.url) + "/api/admin/item"
            headers = {
                'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
                'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
            }
            synced_product_ids = []
            Error_Message = []
            for product in synced_products:
                    food_king_id_categ = 0
                    food_king_id_tax = 0
                    if product.taxes_id:
                        food_king_id_tax = product.taxes_id[0].food_king_id
                    if product.pos_categ_ids:
                        food_king_id_categ = product.pos_categ_ids[0].food_king_id
                        image_data= None
                        if product.image_1920:
                            image_data = base64.b64decode(product.image_1920)

                        if image_data:
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                                temp_file.write(image_data)
                                temp_file_path = temp_file.name

                            files = [('image', ('Foodking.png', open(temp_file_path, 'rb'), 'image/png'))]
                        else : 
                                files = []

                        payload = {
                            "name": product.name,
                            "price": product.list_price,
                            "item_category_id": food_king_id_categ,
                            "tax_id": food_king_id_tax if food_king_id_tax != 0 else None,
                            "item_type":  5 if product.item_type == 'veg' else 10,
                            "is_featured": 10  if product.is_featured == 'no' else 5,
                            "description": product.description or '',
                            "caution": product.caution or '',
                            "order": product.sequence,
                            "status": 5 if product.food_king_active else 10 ,
                        }
                        print(payload,"sssssssssssss")
                        try:
                            response = requests.request("POST", url, headers=headers, data=payload, files=files)
                            response_data = response.json()
                            if 'message' in response_data:
                                Error_Message.append("The Following Products is not sync there are some issues")
                                Error_Message.append('('+product.name+')' + ' ' + response_data['message'])
                                
                            if 'data' in response_data:
                                food_king_id = response_data['data']['id']
                                product.write({'food_king_id': food_king_id})
                                synced_product_ids.append(product.id)

                                artibutes = self.env['product.attribute'].search([])
                                artibuteline=self.env['product.template.attribute.value'].search([])
                                print(artibuteline,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
                                synced_artibutes = self.env['product.attribute'].search([('food_king_id', '=', 0)])
                                url_atribute =(self.url or Foodking_Ids.url)   + "/api/admin/setting/item-attribute"
                            
                                synced_artibutes_ids = []
                                for artibutes in synced_artibutes:
                                        payload_atribute = {
                                            "name": artibutes.name,
                                            "status": 5 if artibutes.food_king_active else 10
                                        }
                                        try:
                                            response_atribute = requests.post(url_atribute, headers=headers, data=payload_atribute)
                                            response_data_atribute = response_atribute.json()
                                            print(response_data_atribute,"dddddddddddddkkkkkkkkkkkkklllllllllllllnnnnnnmmmmmmmmmmmmmm")
                                            if 'data' in response_data_atribute:
                                                food_king_id_atribute = response_data_atribute['data']['id']
                                                artibutes.write({'food_king_id': food_king_id_atribute})
                                                synced_artibutes_ids.append(artibutes.id)

                                        except requests.exceptions.RequestException as e:
                                            return {'error': str(e)}
                                        
                                for attribute_line in product.attribute_line_ids:
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
                                                    url_get_id_atribute2  = (self.url or Foodking_Ids.url)+f"/api/admin/item/variation/{product.food_king_id}"
                                                    response_get_id_atribute2  = requests.request("POST", url_get_id_atribute2 , headers=headers , data=payload_atribute2 )
                                                    response_data_atribute2  = response_get_id_atribute2 .json()
                                                    if 'data' in response_data_atribute2 :
                                                        food_king_id_atribute2  = response_data_atribute2 ['data']['id']
                                                        print(food_king_id_atribute2 ,"kkkkkkkjjjjjjjjjjjjjjjjjjjjjjjjjjjjdddddddddddddddd")
                                                        value_id.write({'food_king_id': food_king_id_atribute2 })
                                                        line_ids_price.write({'food_king_id': food_king_id_atribute2 })
                                                        product.write({'food_king_id_variant':food_king_id_atribute2})

                                
                                
                                synced_topping = product.product_variant_ids.topping_ids
                                for topping in synced_topping:
                                    payload_topping = {
                                        "name": topping.name,
                                        "price": topping.list_price,
                                        "status": 5
                                    }
                                    try:
                                        url = (self.url or Foodking_Ids.url)+f"/api/admin/item/extra/{food_king_id}"
                                        response_topping = requests.post(url, headers=headers, data=payload_topping)
                                        response_data_topping = response_topping.json()
                                        print(response_data_topping,payload,'food_king_id_topping======================================================>>>>>>')
                                            
                                        if 'data' in response_data_topping:
                                            food_king_id_topping = response_data_topping['data']['id']
                                            product.write({'food_king_id_topping': food_king_id_topping})
                                            topping.write({'food_king_id_topping': food_king_id_topping})
                                
                                    

                                    except requests.exceptions.RequestException as e:
                                        print( str(e))
                                        pass

                                
                        except requests.exceptions.RequestException as e:
                            print( str(e))
                            pass
        
      
        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        dic_msg = "Product Synced Successfully." + os.linesep + '\n'.join(Error_Message)
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
 
   #  sync customer  

    def get_customer_from_api(self, cron_mode=True):
        Foodking_Ids_data = self.env['food_king.food_king'].sudo().search([])
        for Foodking_Ids  in Foodking_Ids_data :
                self.get_admin_customer_from_api()
                url = (self.url or Foodking_Ids.url) + "/api/admin/customer"
                headers = {
                    'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
                    'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
                }
                existing_customer_ids = [customer.food_king_id_res for customer in self.env['res.partner'].search([])]

                response = requests.request("GET", url, headers=headers)
                response.raise_for_status()
                customers = response.json().get('data', [])
                print(customers,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
                for customer in customers:
                    base64_image = self.get_base64_from_url(customer.get('image'))
                    vals = {
                        "name": customer.get('name'),
                        "email": customer.get('email'),
                        "phone": customer.get('phone'),
                        'food_king_id_res': customer.get('id'),
                        'image_1920': base64_image,
                    }
                    if customer.get('id') in existing_customer_ids:
                        print('no found')
                    else:
                        self.env['res.partner'].create(vals)

        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        dic_msg = 'Customers Synced Successfully'
        context['message'] = dic_msg
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }

   #  sync customer   

    def get_admin_customer_from_api(self, cron_mode=True):
        Foodking_Ids_data = self.env['food_king.food_king'].sudo().search([])
        for Foodking_Ids  in Foodking_Ids_data :
                url = (self.url or Foodking_Ids.url) + "/api/admin/administrator?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
                headers = {
                    'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
                    'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
                }
                existing_customer_ids = [customer.food_king_id_res for customer in self.env['res.partner'].search([])]

                try:
                    response = requests.request("GET", url, headers=headers)
                    response.raise_for_status()
                    customers = response.json().get('data', [])
                    print(customers,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
                    for customer in customers:
                        base64_image = self.get_base64_from_url(customer.get('image'))
                        vals = {
                            "name": customer.get('name'),
                            "email": customer.get('email'),
                            "phone": customer.get('phone'),
                            'food_king_id_res': customer.get('id'),
                            'image_1920': base64_image,
                        }
                        if customer.get('id') in existing_customer_ids:
                            print('hhhh')
                        else:
                            self.env['res.partner'].create(vals)

                except requests.exceptions.RequestException as e:
                    return {'error': str(e)}
  
   #  sync category

    def sync_all_category(self, cron_mode=True):
        Foodking_Ids_data = self.env['food_king.food_king'].sudo().search([])
        for Foodking_Ids  in Foodking_Ids_data :
            synced_categories = self.env['pos.category'].search([('food_king_id', '=', 0)])
            url = (self.url or Foodking_Ids.url) + "/api/admin/setting/item-category?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
            headers = {
                'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
                'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
                # 'Content-Type': 'application/json',
            }
            
            Error_Message = []
            files=[]
            for category in synced_categories:
                image_data = None
                if category.image_128:
                    image_data = base64.b64decode(category.image_128)
                    if image_data:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                            temp_file.write(image_data)
                            temp_file_path = temp_file.name

                            files = [('image', ('Foodking.png', open(temp_file_path, 'rb'), 'image/png'))]
                    else : 
                        files = []
            
                payload = {
                    "name": category.name,
                    "status": 5,
                    "description": category.name
                }
                try:
                    response = requests.request("POST", url, headers=headers, data=payload,files=files)
                    response_data = response.json()
                    print(response_data), "sssssssssssssssssssssss"
                    if 'message' in response_data:
                            Error_Message.append("The Following Categories is not sync there are some issues")
                            Error_Message.append('('+category.name+')' + ' ' + response_data['message'])
                                
                    if 'data' in response_data:
                        food_king_id = response_data['data']['id']
                        category.write({'food_king_id': food_king_id})
                except requests.exceptions.RequestException as e:
                            print( str(e))
                            pass

        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        context['message'] = "Categories Synced Successfully." + os.linesep + '\n'.join(Error_Message)
        return {
            'name': 'Success',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'sh.message.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
            }

   #  sync all taxes          
     
    def sync_all_tax(self, cron_mode=True):
            Foodking_Ids_data = self.env['food_king.food_king'].sudo().search([])
            for Foodking_Ids  in Foodking_Ids_data :
                taxes = self.env['account.tax'].search([])
                synced_taxes = self.env['account.tax'].search([('food_king_id', '=', 0)])
                url = (self.url or Foodking_Ids.url) + "/api/admin/setting/tax"
                headers = {
                    'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
                    'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
                    'Content-Type': 'application/json',
                }
                Error_Message = []
                for tax in synced_taxes:
                    if  synced_taxes != []:
                        payload = json.dumps({
                            "name": tax.name,
                            "code": tax.name,
                            "tax_rate": tax.amount,
                            "status": 5
                        })

                        try:
                            response = requests.post(url, headers=headers, data=payload)
                            response_data = response.json()
                            print(response_data,'llllllllllllllllllllll')
                            if 'message' in response_data:
                                Error_Message.append("The Following Taxes is not sync there are some issues")
                                Error_Message.append('('+tax.name+')' + ' ' + response_data['message'])
                                
                            if 'data' in response_data:
                                food_king_id = response_data['data']['id']
                                tax.write({'food_king_id': food_king_id})
                        
                            

                        except requests.exceptions.RequestException as e:
                            print( str(e))
                            pass
            
            view = self.env.ref('sh_message.sh_message_wizard')
            context = dict(self._context or {})
            dic_msg = "Taxes Synced Successfully." + os.linesep + '\n'.join(Error_Message)
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
    
   #  sync pos order

    def get_pos_order_from_api(self, cron_mode=True):
            success_true = False
            self.get_online_order_from_api()
            Foodking_Ids_data = self.env['food_king.food_king'].sudo().search([])
            for Foodking_Ids  in Foodking_Ids_data :
                url = f"{self.url or Foodking_Ids.url}/api/admin/table-order?paginate=1&page=1&per_page=10&order_column=id&order_by=desc&order_type=20"
                headers = {
                        'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
                        'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
                    }
                existing_pos_order_ids = [pos.food_king_id for pos in self.env['pos.order'].search([])]

                response = requests.get(url, headers=headers)
                pos_orders = response.json().get('data', [])
                for pos_data1 in pos_orders:
                    if pos_data1['id'] not in  existing_pos_order_ids:
                        data_filter_by_branch = self.company_id.branch_id.food_king_id or Foodking_Ids.company_id.branch_id.food_king_id
                        if data_filter_by_branch == pos_data1['branch_id']:
                                url_get_id = f"{self.url or Foodking_Ids.url}/api/admin/table-order/show/{pos_data1['id']}"
                                response_get_id = requests.get(url_get_id, headers=headers)
                                pos_data = response_get_id.json().get('data', {})

                                customer_ids = self.env['res.partner'].search([('food_king_id_res', '=', pos_data['user']['id'])]).mapped('id')
                                line_vals = []
                                instruction= []
                                for posid in pos_data['order_items']:
                                    product_ids = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('id')
                                    product_Variant_ids = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('product_variant_id')
                                    product_Variants_ids = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('product_variant_ids')
                                    products_name = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('name')
                                    products_tax = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('taxes_id')
                                    print(product_Variant_ids,"product_Variant_ids",product_Variants_ids,"product_Variants_ids",products_name,"products_name")
                                    if product_ids or products_name or products_tax:
                                        product_id = product_ids[0]
                                        product_name = products_name[0]
                                        product_tax = products_tax[0] if products_tax else ''
                                        price = re.sub(r'[^\d.]+', '', posid['price'])
                                        discount = re.sub(r'[^\d.]+', '', posid['discount'])
                                        variation_names = [variation['name'] for variation in posid['item_variations']]
                                        full_product_name = product_name+' (' +''.join(variation_names)+')' if variation_names else product_name
                                        instruction.append(full_product_name + ' : ' + posid['instruction'])
                                        uid_counter = 1
                                        variation_ids = [variation['id'] for variation in posid['item_variations']]
                                        product_product_ids = [item_id['product_template_variant_value_ids'] for item_id in product_Variants_ids]
                                        extras_ids = [variation['id'] for variation in posid['item_extras']]
                                        print(extras_ids,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
                                        topping_ids = self.env['product.product'].search([('food_king_id_topping', 'in', extras_ids)]).mapped('topping_ids')
                                        line_topping_ids = [data.id for data in topping_ids]
                                        print(product_tax.price_include,"lllllllllllljjjjjjjjjjjjjjjjjjjjjjjjjlllllllllllll")
                                        line_topping_ids_price = re.sub(r'[^\d.]+', '', posid['item_extra_currency_total'])
                                        item_variation_currency_total = re.sub(r'[^\d.]+', '', posid['item_variation_currency_total'])
                                        if product_Variants_ids:
                                                printed_ids = set()
                                                for item_id in product_Variants_ids:
                                                    if posid['item_variations']:
                                                            product_id = item_id.food_king_id
                                                            if product_id not in printed_ids:
                                                                printed_ids.add(product_id)
                                                                
                                                                if product_id == posid['item_id']:
                                                                    line_vals.append((0, 0, {
                                                                        'uuid': uid_counter,
                                                                        'line_topping_ids':line_topping_ids,
                                                                        'company_id': self.company_id.id or Foodking_Ids.company_id.id,
                                                                        'product_id': item_id.id,
                                                                        'full_product_name': full_product_name,
                                                                        'qty': posid['quantity'],
                                                                        'price_unit': float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total) if product_tax.price_include and product_tax else (float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total))/((100+float(product_tax.amount))/100) if product_tax else float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total) ,
                                                                        'discount': float(discount),
                                                                        'tax_ids': [(6, 0, [int(product_tax.id)])] if product_tax and product_tax.id else [],
                                                                        'price_subtotal':float(posid['total_convert_price'])/((100+float(product_tax.amount))/100) if product_tax else 0,
                                                                        'price_subtotal_incl': float(posid['total_convert_price']),
                                                                        'customer_note':posid['instruction']
                                                                    }))
                                                                    uid_counter += 1
                                                                
                                                    if posid['item_variations'] == []:
                                                                    line_vals.append((0, 0, {
                                                                                        'company_id': self.company_id.id or Foodking_Ids.company_id.id,
                                                                                        'product_id': item_id.id,
                                                                                        'line_topping_ids':line_topping_ids,
                                                                                        'full_product_name': full_product_name,
                                                                                        'qty': posid['quantity'],
                                                                                        'price_unit': float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total) if product_tax.price_include and product_tax else (float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total))/((100+float(product_tax.amount))/100) if product_tax else float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total) ,
                                                                                        'discount': float(discount),
                                                                                        'tax_ids': [(6, 0, [int(product_tax)])] if product_tax and product_tax.id else [],
                                                                                        'price_subtotal':float(posid['total_convert_price'])/((100+float(product_tax.amount))/100) if product_tax else 0,
                                                                                        'price_subtotal_incl': float(posid['total_convert_price']),
                                                                                        'customer_note':posid['instruction']
                                                                                    }))
                                if customer_ids:
                                    food_king_floor = self.env['restaurant.floor'].search([('name', '=', self.point_of_sale.name or Foodking_Ids.point_of_sale.name)], limit=1)
                                    search_table = self.env['restaurant.table'].search([('name', '=',pos_data['table_name'] ), ('floor_id', '=', food_king_floor.id)]).mapped('id')
                                    customer_id = customer_ids[0]
                                    table_id = 0
                                    config_id = self.point_of_sale.id or Foodking_Ids.point_of_sale.id
                                    if search_table:
                                        table_id = search_table[0]
                                    total_tax_currency_price = re.sub(r'[^\d.]+', '', pos_data['total_tax_currency_price'])
                                    subtotal_currency_price = re.sub(r'[^\d.]+', '', pos_data['subtotal_currency_price'])
                                    search_pos_session = self.env['pos.session'].sudo().search([
                                            ('state', '=', 'opened'), 
                                            ('company_id', '=', self.company_id.id or Foodking_Ids.company_id.id),
                                            ('config_id', '=', self.point_of_sale.id or Foodking_Ids.point_of_sale.id)
                                        ])
                                    if config_id:
                                        if search_pos_session:
                                            session_name = search_pos_session[0].name
                                            result = f"Order {session_name.split('/')[1]}-00{str(config_id)}-{pos_data['order_serial_no']}"
                                            vals = {
                                                'food_king_id':pos_data['id'],
                                                'name': f"{self.point_of_sale.name}/000{str(config_id)}",
                                                'config_id' : config_id,
                                                'partner_id': customer_id,
                                                'amount_total': float(subtotal_currency_price),
                                                'session_id': search_pos_session[0].id,
                                                'company_id': self.company_id.id or Foodking_Ids.company_id.id,
                                                'amount_tax':  float(total_tax_currency_price),
                                                'amount_paid': float(subtotal_currency_price),
                                                'amount_return': 0.0,
                                                'table_id':table_id,
                                                'status':'Table Order',
                                                'pos_reference' : result,
                                                'state': 'draft'  ,
                                                'lines': line_vals,
                                                'is_accepted':True if pos_data['payment_status'] == 5 else False,
                                                'note':'\n'.join(instruction)
                                            }
                                            self.env['pos.order'].sudo().create(vals)
                                            success_true = True
                                            group = self.env.ref('food_king.group_food_king_user')
                                            users = self.env['res.users'].search([('groups_id', 'in', [group.id])])

                                            for user in users:
                                                message = self.env['mail.message'].create({
                                                    'author_id': 1,
                                                    'model': 'discuss.channel',
                                                    'res_id': 1,
                                                    'message_type': 'comment',
                                                    'body': f"New order. Order ID: {result}",
                                                    'subtype_id': self.env.ref('mail.mt_comment').id,
                                                    'record_name': "Food King Message",
                                                })
                    
                                        else :
                                            raise UserError(('Please open the session'))
                                        
                                    else :
                                        raise UserError(('Please select point of sale'))
                                else:
                                    view = self.env.ref('sh_message.sh_message_wizard')
                                    context = dict(self._context or {})
                                    dic_msg =  "Customer Not Synced"
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
                   
                view = self.env.ref('sh_message.sh_message_wizard')
                context = dict(self._context or {})
                dic_msg =  "Order Synced Successfully"
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
               
   #  sync online order

    def get_online_order_from_api(self, cron_mode=True):
            # for compnay_id  in companies :
            Foodking_Ids_data = self.env['food_king.food_king'].sudo().search([])
            for Foodking_Ids  in Foodking_Ids_data :
                    url = f"{self.url or Foodking_Ids.url}/api/admin/online-order?paginate=1&page=1&per_page=10&order_column=id&order_by=desc&excepts=15|20"
                    headers = {
                        'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
                        'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
                    }
                    existing_pos_order_ids = [pos.food_king_id for pos in self.env['pos.order'].search([])]
                    try:
                        response = requests.get(url, headers=headers)
                        pos_orders = response.json().get('data', [])
                        for pos_data1 in pos_orders:
                            if pos_data1['id'] not in  existing_pos_order_ids:
                                data_filter_by_branch = self.company_id.branch_id.food_king_id or Foodking_Ids.company_id.branch_id.food_king_id
                                if data_filter_by_branch == pos_data1['branch_id']:
                                    print('mubeen 1')
                                    url_get_id = f"{self.url or Foodking_Ids.url}/api/admin/online-order/show/{pos_data1['id']}"
                                    response_get_id = requests.get(url_get_id, headers=headers)
                                    pos_data = response_get_id.json().get('data', {})
                                    customer_ids = self.env['res.partner'].sudo().search([('food_king_id_res', '=', pos_data1['customer']['id'])]).mapped('id')
                                    line_vals = []
                                    instruction= []
                                    for posid in pos_data['order_items']:
                                        product_ids = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('id')
                                        product_Variants_ids = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('product_variant_ids')
                                        products_name = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('name')
                                        products_tax = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('taxes_id')
                                        if product_ids or products_name or products_tax:
                                            product_id = product_ids[0]
                                            product_name = products_name[0]
                                            product_tax = products_tax[0] if products_tax else ''
                                            price = re.sub(r'[^\d.]+', '', posid['price'])
                                            discount = re.sub(r'[^\d.]+', '', posid['discount'])
                                            line_topping_ids_price = re.sub(r'[^\d.]+', '', posid['item_extra_currency_total']) if posid['item_extra_currency_total'] else 0
                                            item_variation_currency_total = re.sub(r'[^\d.]+', '', posid['item_variation_currency_total']) if posid['item_variation_currency_total'] else 0
                                            variation_names = [variation['name'] for variation in posid['item_variations']]
                                            full_product_name = product_name+' (' +','.join(variation_names)+')' if variation_names else product_name
                                            instruction.append(full_product_name + ' : ' + posid['instruction'])
                                            uid_counter = 1
                                            variation_ids = [variation['id'] for variation in posid['item_variations']]
                                            extras_ids = [variation['id'] for variation in posid['item_extras']]
                                            topping_ids = self.env['product.product'].search([('food_king_id_topping', 'in', extras_ids)]).mapped('topping_ids')
                                            line_topping_ids = [data.id for data in topping_ids]
                                        
                                            print(line_topping_ids_price,item_variation_currency_total,product_Variants_ids, "lllllllllllljjjjjjjjjjjjjjjjjjjjjjjjjlllllllllllll")
                                            if product_Variants_ids:
                                                printed_ids = set()
                                                for item_id in product_Variants_ids:
                                                    if posid['item_variations']:
                                                            product_id = item_id.food_king_id
                                                            if product_id not in printed_ids:
                                                                printed_ids.add(product_id)
                                                                print(item_id.id,"qqqqqqqqqqqqqqqqqqqqqqqqqq",item_id.name,"eeeeeeeeeeeeeeeeeeeeeeeee")
                                                                if product_id == posid['item_id']:
                                                                    line_vals.append((0, 0, {
                                                                        'uuid': uid_counter,
                                                                        'line_topping_ids':line_topping_ids,
                                                                        'company_id': self.company_id.id or Foodking_Ids.company_id.id,
                                                                        'product_id': item_id.id,
                                                                        'full_product_name': full_product_name,
                                                                        'qty': posid['quantity'],
                                                                        'price_unit':float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total) if product_tax.price_include and product_tax else (float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total))/((100+float(product_tax.amount))/100) if product_tax else float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total) ,
                                                                        'discount': float(discount),
                                                                        'tax_ids': [(6, 0, [int(product_tax.id)])] if product_tax and product_tax.id else [],
                                                                        'price_subtotal': float(posid['total_convert_price'])/((100+float(product_tax.amount))/100) if product_tax else 0,
                                                                        'price_subtotal_incl': float(posid['total_convert_price']),
                                                                        'customer_note':posid['instruction']
                                                                    }))
                                                                    uid_counter += 1
                                                                
                                                    if posid['item_variations'] == []:
                                                                    line_vals.append((0, 0, {
                                                                                        'company_id': self.company_id.id or Foodking_Ids.company_id.id,
                                                                                        'product_id': item_id.id,
                                                                                        'line_topping_ids':line_topping_ids,
                                                                                        'full_product_name': full_product_name,
                                                                                        'qty': posid['quantity'],
                                                                                        'price_unit':float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total) if product_tax.price_include and product_tax else (float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total))/((100+float(product_tax.amount))/100) if product_tax else float(price)  + float(line_topping_ids_price) + float(item_variation_currency_total),
                                                                                        'discount': float(discount),
                                                                                        'tax_ids': [(6, 0, [int(product_tax)])] if product_tax and product_tax.id else [],
                                                                                        'price_subtotal':float(posid['total_convert_price'])/((100+float(product_tax.amount))/100) if product_tax else 0,
                                                                                        'price_subtotal_incl': float(posid['total_convert_price']),
                                                                                        'customer_note':posid['instruction']
                                                                                    }))
                                    if customer_ids:
                                        customer_id = customer_ids[0]
                                        food_king_floor = self.env['restaurant.floor'].search([('name', '=', self.point_of_sale.name or Foodking_Ids.point_of_sale.name)], limit=1)
                                        search_table = self.env['restaurant.table'].search([('name', '=', 'Delivery Table'), ('floor_id', '=', food_king_floor.id)]).mapped('id')
                                        config_id = self.point_of_sale.id or Foodking_Ids.point_of_sale.id 
                                        total_tax_currency_price = re.sub(r'[^\d.]+', '', pos_data['total_tax_currency_price'])
                                        total_currency_price = re.sub(r'[^\d.]+', '', pos_data['total_currency_price'])
                                        delivery_charges =  self.env['product.product'].sudo().search([('name', '=', 'Delivery Charges')])
                                        delivery_charge_currency_price = re.sub(r'[^\d.]+', '', pos_data['delivery_charge_currency_price'])
                                        print(delivery_charges,delivery_charges.id,delivery_charges.name,"mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm")
                                        line_vals.append((0, 0, {
                                            'product_id': delivery_charges.id,
                                            'full_product_name': delivery_charges.name,
                                            'qty': 1,
                                            'company_id': self.company_id.id or Foodking_Ids.company_id.id,
                                            'price_unit': float(delivery_charge_currency_price) if delivery_charges.taxes_id and delivery_charges.taxes_id.price_include  else float(delivery_charge_currency_price)/((100+delivery_charges.taxes_id.amount )/100) if delivery_charges.taxes_id else float(delivery_charge_currency_price) ,
                                            'tax_ids' : [(4, delivery_charges.taxes_id.id)] if delivery_charges != '' and delivery_charges.taxes_id.id else [],
                                            'price_subtotal': float(delivery_charge_currency_price)/((100+delivery_charges.taxes_id.amount )/100) if delivery_charges.taxes_id else 0,
                                            'price_subtotal_incl':float(delivery_charge_currency_price) if delivery_charges.taxes_id and delivery_charges.taxes_id.price_include else float(delivery_charge_currency_price) + (float(delivery_charge_currency_price) * delivery_charges.taxes_id.amount) / 100
                                        }))
                                        search_pos_session = self.env['pos.session'].sudo().search([
                                            ('state', '=', 'opened'), 
                                            ('company_id', '=', self.company_id.id or Foodking_Ids.company_id.id),
                                            ('config_id', '=', self.point_of_sale.id or Foodking_Ids.point_of_sale.id)
                                        ])
                                        if config_id:
                                            if search_pos_session:
                                                    session_name = search_pos_session[0].name
                                                    result = f"Order {session_name.split('/')[1]}-00{str(config_id)}-{pos_data['order_serial_no']}"
                                                    vals = {
                                                        'food_king_id':pos_data['id'],
                                                        'name': f"{self.point_of_sale.name or Foodking_Ids.point_of_sale.name}/000{str(config_id)}",
                                                        'config_id' : config_id,
                                                        'partner_id': customer_id,
                                                        'amount_total': sum([line[2]['price_subtotal_incl'] for line in line_vals]),
                                                        'session_id': search_pos_session[0].id,
                                                        'company_id': self.company_id.id or Foodking_Ids.company_id.id,
                                                        'amount_tax':  float(total_tax_currency_price),
                                                        'amount_paid': sum([line[2]['price_subtotal_incl'] for line in line_vals]) if pos_data['payment_status'] == 5 else 0,
                                                        'amount_return': 0.0,
                                                        'status':'Online Order',
                                                        'pos_reference' : result,
                                                        'state':  'draft'  ,
                                                        'lines': line_vals,
                                                        'note':'\n'.join(instruction),
                                                        'tracking_number':803,
                                                        'session_move_id':7,
                                                        'is_accepted':True if pos_data['payment_status'] == 5 else False,
                                                        'table_id': search_table[0],
                                                    }
                                                    print(vals,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
                                                    self.env['pos.order'].sudo().create(vals)
                                                    group = self.env.ref('food_king.group_food_king_user')
                                                    users = self.env['res.users'].search([('groups_id', 'in', [group.id])])

                                                    for user in users:
                                                        message = self.env['mail.message'].create({
                                                            'author_id': 1,
                                                            'model': 'discuss.channel',
                                                            'res_id': 1,
                                                            'message_type': 'comment',
                                                            'body':f"New order. Order ID: {result}",
                                                            'subtype_id': self.env.ref('mail.mt_comment').id,
                                                            'record_name': "Food King Message",
                                                        })
                                                    
                                                
                                            else :
                                                raise UserError(('Please open the session'))
                                                
                                        else :
                                            raise UserError(('Please select point of sale'))
                                    else:
                                        view = self.env.ref('sh_message.sh_message_wizard')
                                        context = dict(self._context or {})
                                        dic_msg =  "Customer Not Synced"
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

                    except requests.exceptions.RequestException as e:
                        return {'error': str(e)}
  
   #  sync floor

    def get_floors_from_api(self, cron_mode=True):
        Foodking_Ids_data = self.env['food_king.food_king'].sudo().search([])
        for Foodking_Ids  in Foodking_Ids_data :
            url = (self.url or Foodking_Ids.url) + "/api/admin/dining-table?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
            headers = {
                'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
                'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
            }
            existing_floor_ids = [floor.food_king_id for floor in self.env['restaurant.table'].search([])]
            
        
            if self.point_of_sale:
                food_king_floor = self.env['restaurant.floor'].search([('name', '=', self.point_of_sale.name)], limit=1)
                if not food_king_floor:
                    food_king_floor = self.env['restaurant.floor'].create({
                        'name': self.point_of_sale.name,
                        'pos_config_ids': [(4, self.point_of_sale.id or Foodking_Ids.point_of_sale.id )]  
                    })
                else:
                    food_king_floor.write({
                        'pos_config_ids': [(4, self.point_of_sale.id or Foodking_Ids.point_of_sale.id )]  
                    })
                food_king_pos = self.env['pos.config'].search([('name', '=', self.point_of_sale.name or Foodking_Ids.point_of_sale.name )], limit=1)
            else :
                raise UserError(('Please select point of sale'))
            delivery_table = self.env['restaurant.table'].search([('name', '=', 'Delivery Table'), ('floor_id', '=', food_king_floor.id)], limit=1)
            if not delivery_table:
                vals = {
                        'name': 'Delivery Table',
                        'seats': 4,
                        'floor_id': food_king_floor.id if food_king_floor else False,
                    }
                self.env['restaurant.table'].create(vals)

                response = requests.get(url, headers=headers)
                response.raise_for_status()
                floors = response.json().get('data', [])
                for floor in floors:
                    print(floor.get('id'),floor.get('name'),existing_floor_ids )
                    vals = {
                        'name': floor.get('name'),
                        'seats': floor.get('size'),
                        'food_king_id': floor.get('id'),
                        'floor_id': food_king_floor.id if food_king_floor else False,
                    }
                    if floor.get('id') in existing_floor_ids:
                        print('')
                    else :
                        self.env['restaurant.table'].create(vals)
                

            view = self.env.ref('sh_message.sh_message_wizard')
            context = dict(self._context or {})
            dic_msg =  "Table synced successfully."
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
     
   #  sync branch

    def get_branch_from_api(self, cron_mode=True):
        Foodking_Ids_data = self.env['food_king.food_king'].sudo().search([])
        for Foodking_Ids  in Foodking_Ids_data :
            url = (self.url or Foodking_Ids.url) + "/api/admin/setting/branch?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
            headers = {
                'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
                'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
            }
            existing_branch_ids = [branch.food_king_id for branch in self.env['food.king.branch'].search([])]

            response = requests.request("GET", url, headers=headers)
            response.raise_for_status()
            branches = response.json().get('data', [])
            for branch_data in branches:
                vals = {
                    'name': branch_data.get('name'),
                    'email': branch_data.get('email'),
                    'phone': branch_data.get('phone'),
                    'latitude': float(branch_data.get('latitude')),
                    'longitude': float(branch_data.get('longitude')),
                    'city': branch_data.get('city'),
                    'state': branch_data.get('state'),
                    'zip_code': branch_data.get('zip_code'),
                    'status': int(branch_data.get('status')),
                    'food_king_id': branch_data.get('id') 
                }

                if branch_data.get('id') in existing_branch_ids:
                    print('Branch already exists')
                else:
                    self.env['food.king.branch'].create(vals)
            view = self.env.ref('sh_message.sh_message_wizard')
            context = dict(self._context or {})
            dic_msg =  "Branches synced successfully."
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
   

    

        

            
            