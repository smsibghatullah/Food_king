import requests
from odoo import models, fields, api
import json
from odoo.exceptions import AccessError,UserError
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
import re
import base64
import tempfile

class food_king(models.Model):
    _name = 'food_king.food_king'

    username = fields.Char('Username')
    password = fields.Char('Password', widget='password')
    url = fields.Char('URL')
    auth_token = fields.Char('Token')
    license_key = fields.Char('License Key')


    def get_base64_from_url(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            base64_image = base64.b64encode(response.content).decode('utf-8')
            return base64_image
        except requests.exceptions.RequestException as e:
            return None
        
    def get_token(self):
        login_url = self.url + "/api/auth/login"
        headers = {
            'Content-Type': 'application/json',
             'Authorization': '',
             'X-Api-Key':self.license_key or '',
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
        

    def sync_all_products(self, cron_mode=True):
        synced_products = self.env['product.template'].search([('food_king_id', '=', 0)])
        url = self.url + "/api/admin/item"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'X-Api-Key':self.license_key or '',
            'Content-Type': 'application/json',
        }
        print(synced_products,"fffffffffffffffff")
        if not synced_products :
                    view = self.env.ref('sh_message.sh_message_wizard')
                    context = dict(self._context or {})
                    dic_msg = "Product Already Synced"
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
        synced_product_ids = []
        for product in synced_products:
                food_king_id_categ = 0
                food_king_id_tax = 0
                if product.pos_categ_ids:
                    food_king_id_categ = product.pos_categ_ids[0].food_king_id
                if product.taxes_id:
                    food_king_id_tax = product.taxes_id[0].food_king_id

                    image_base64 = ""
                    if product.image_1920:
                        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                            temp_file.write(product.image_1920)
                            temp_file_path = temp_file.name
                        with open(temp_file_path, "rb") as image_file:
                            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                    payload = json.dumps({
                        "name": product.name,
                        "price": product.list_price,
                        "item_category_id": food_king_id_categ,
                        "tax_id": food_king_id_tax,
                        "item_type":  5 if product.item_type == 'veg' else 10,
                        "is_featured": 10  if product.is_featured == 'no' else 5,
                        "description": product.description or '',
                        "caution": product.caution or '',
                        "order": product.sequence,
                        "status": 5,
                        "preview": image_base64
                    })

                    try:
                        response = requests.post(url, headers=headers, data=payload)
                        response_data = response.json()
                        print(response_data,"ppppppppppppppppppppppppppppp")

                        if 'data' in response_data:
                            food_king_id = response_data['data']['id']
                            product.write({'food_king_id': food_king_id})
                            synced_product_ids.append(product.id)

                            
                    except requests.exceptions.RequestException as e:
                        return {'error': str(e)}
        
        if synced_product_ids:
                        view = self.env.ref('sh_message.sh_message_wizard')
                        context = dict(self._context or {})
                        dic_msg = response_data.get('message', "Product Synced Successfully")
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
        else:
            return {'message': 'No new Product to sync.'}
    
    
    def get_customer_from_api(self, cron_mode=True):
        self.get_admin_customer_from_api()
        url = self.url + "/api/admin/customer"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'X-Api-Key': self.license_key or '',
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
                    view = self.env.ref('sh_message.sh_message_wizard')
                    context = dict(self._context or {})
                    dic_msg = 'Customer Already Synced'
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

        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
            
    def get_admin_customer_from_api(self, cron_mode=True):
        url = self.url + "/api/admin/administrator?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'X-Api-Key': self.license_key or '',
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
# sync category

    def sync_all_category(self, cron_mode=True):
        synced_categories = self.env['pos.category'].search([('food_king_id', '=', 0)])
        url = self.url + "/api/admin/setting/item-category?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'X-Api-Key':self.license_key or '',
            'Content-Type': 'application/json',
        }
        if not synced_categories :
                    view = self.env.ref('sh_message.sh_message_wizard')
                    context = dict(self._context or {})
                    dic_msg = "Categories Already Synced"
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
        synced_categories_ids = []
        for category in synced_categories:
            payload = json.dumps({
                "name": category.name,
                "status": 5,
                "description": category.name
            })
            try:
                response = requests.post(url, headers=headers, data=payload)
                response_data = response.json()
                print(response_data), "sssssssssssssssssssssss"
                if 'data' in response_data:
                    food_king_id = response_data['data']['id']
                    category.write({'food_king_id': food_king_id})
                    synced_categories_ids.append(category.id)
            except requests.exceptions.RequestException as e:
                return {'error': str(e)}

        if synced_categories_ids:
            view = self.env.ref('sh_message.sh_message_wizard')
            context = dict(self._context or {})
            context['message'] = "Categories Synced Successfully"
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
        else:
            return {'message': 'No new categories to sync.'}
       
    

   #   sync all taxes          # 
     
    def sync_all_tax(self, cron_mode=True):
            taxes = self.env['account.tax'].search([])
            synced_taxes = self.env['account.tax'].search([('food_king_id', '=', 0)])
            url = self.url + "/api/admin/setting/tax"
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'X-Api-Key':self.license_key or '',
                'Content-Type': 'application/json',
            }
            print(synced_taxes,"fffffffffffffffff")
            if not synced_taxes :
                        view = self.env.ref('sh_message.sh_message_wizard')
                        context = dict(self._context or {})
                        dic_msg = "Taxes Already Synced"
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
            synced_tax_ids = []
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

                        if 'data' in response_data:
                            food_king_id = response_data['data']['id']
                            tax.write({'food_king_id': food_king_id})
                            synced_tax_ids.append(tax.id)

                    except requests.exceptions.RequestException as e:
                        return {'error': str(e)}
        
            if synced_tax_ids:
                        view = self.env.ref('sh_message.sh_message_wizard')
                        context = dict(self._context or {})
                        dic_msg = response_data.get('message', "Taxes Synced Successfully")
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
            else:
                return {'message': 'No new Taxes to sync.'}
    
    # sync pos order

    def get_pos_order_from_api(self, cron_mode=True):
            self.get_online_order_from_api()
            url = f"{self.url}/api/admin/table-order?paginate=1&page=1&per_page=10&order_column=id&order_by=desc&order_type=20"
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'X-Api-Key':self.license_key or '',
            }
            existing_pos_order_ids = [pos.food_king_id for pos in self.env['pos.order'].search([])]

            try:
                response = requests.get(url, headers=headers)
                pos_orders = response.json().get('data', [])
                for pos_data in pos_orders:
                    if pos_data['id'] not in  existing_pos_order_ids:
                        url_get_id = f"{self.url}/api/admin/table-order/show/{pos_data['id']}"
                        response_get_id = requests.get(url_get_id, headers=headers)
                        pos_data = response_get_id.json().get('data', {})

                        customer_ids = self.env['res.partner'].search([('food_king_id_res', '=', pos_data['user']['id'])]).mapped('id')
                        line_vals = []
                        for posid in pos_data['order_items']:
                            product_ids = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('id')
                            products_name = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('name')
                            if product_ids or products_name:
                                product_id = product_ids[0]
                                product_name = products_name[0]
                                

                                line_vals.append((0, 0, {
                                    'product_id': product_id,
                                    'full_product_name': product_name,
                                    'qty': posid['quantity'],
                                    'price_unit': posid['price'],
                                    'discount': posid['discount'],
                                    'price_subtotal': posid['total_convert_price'],
                                    'price_subtotal_incl': posid['total_convert_price']
                                }))

                        if customer_ids:
                            search_pos = self.env['pos.config'].search([('name', '=', 'Food King Pos')]).mapped('id')
                            search_table = self.env['restaurant.table'].search([('name', '=',pos_data['table_name'] )]).mapped('id')
                            customer_id = customer_ids[0]
                            if search_pos:
                                table_id = 0
                                config_id = search_pos[0]
                                if search_table:
                                    table_id = search_table[0]
                                
                                vals = {
                                    'food_king_id':pos_data['id'],
                                    'name': pos_data['order_serial_no'],
                                    'config_id' : config_id,
                                    'partner_id': customer_id,
                                    'amount_total': pos_data['subtotal_currency_price'],
                                    'session_id': pos_data['branch']['id'],
                                    'company_id': pos_data['branch']['id'],
                                    'amount_tax': pos_data['total_tax_currency_price'],
                                    'amount_paid': pos_data['subtotal_currency_price'],
                                    'amount_return': 0.0,
                                    'table_id':table_id,
                                    'status':'Table Order',
                                    'pos_reference' : 'Order' + ' ' +pos_data['order_serial_no'],
                                    'state': 'done' if pos_data['status_name'] == 'Delivered' else 'draft' if pos_data['status_name'] == 'Accept' or pos_data['status_name'] == "Pending" else 'paid' ,
                                    'lines': line_vals
                                }
                                self.env['pos.order'].create(vals)

                view = self.env.ref('sh_message.sh_message_wizard')
                context = dict(self._context or {})
                dic_msg =  "Pos Order Synced Successfully"
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


    def get_online_order_from_api(self, cron_mode=True):
            url = f"{self.url}/api/admin/online-order?paginate=1&page=1&per_page=10&order_column=id&order_by=desc&excepts=15|20"
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'X-Api-Key':self.license_key or '',
            }
            existing_pos_order_ids = [pos.food_king_id for pos in self.env['pos.order'].search([])]
            print(existing_pos_order_ids,"dsaaaaaaaaaaaaa")
            try:
                response = requests.get(url, headers=headers)
                pos_orders = response.json().get('data', [])
                for pos_data in pos_orders:
                    print(pos_data['id'],pos_data['order_serial_no'],"kkkkkkkkkkkkkkkkkkkkkkkkkkkk")
                    print(pos_data['id'] not in  existing_pos_order_ids,'aaaaaaaaaaaaaaaa')
                    if pos_data['id'] not in  existing_pos_order_ids:
                        url_get_id = f"{self.url}/api/admin/online-order/show/{pos_data['id']}"
                        response_get_id = requests.get(url_get_id, headers=headers)
                        pos_data = response_get_id.json().get('data', {})
                        print(pos_data,"eeeeeeeeeeeeeeeeeeeeeeeeeeee")
                        customer_ids = self.env['res.partner'].search([('food_king_id_res', '=', pos_data['user']['id'])]).mapped('id')
                        line_vals = []
                        for posid in pos_data['order_items']:
                            product_ids = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('id')
                            products_name = self.env['product.template'].search([('food_king_id', '=', posid['item_id'])]).mapped('name')
                            if product_ids or products_name:
                                product_id = product_ids[0]
                                product_name = products_name[0]
                                

                                line_vals.append((0, 0, {
                                    'product_id': product_id,
                                    'full_product_name': product_name,
                                    'qty': posid['quantity'],
                                    'price_unit': posid['price'],
                                    'discount': posid['discount'],
                                    'price_subtotal': posid['total_convert_price'],
                                    'price_subtotal_incl': posid['total_convert_price']
                                }))

                        if customer_ids:
                            search_pos = self.env['pos.config'].search([('name', '=', 'Food King Pos')]).mapped('id')
                            search_table = self.env['restaurant.table'].search([('name', '=',pos_data['table_name'] )]).mapped('id')
                            customer_id = customer_ids[0]
                            if search_pos:
                                table_id = 0
                                config_id = search_pos[0]
                                if search_table:
                                    table_id = search_table[0]
                                
                                vals = {
                                    'food_king_id':pos_data['id'],
                                    'name': pos_data['order_serial_no'],
                                    'config_id' : config_id,
                                    'partner_id': customer_id,
                                    'amount_total': pos_data['subtotal_currency_price'],
                                    'session_id': pos_data['branch']['id'],
                                    'company_id': pos_data['branch']['id'],
                                    'amount_tax': pos_data['total_tax_currency_price'],
                                    'amount_paid': pos_data['subtotal_currency_price'],
                                    'amount_return': 0.0,
                                    'table_id':table_id,
                                    'status':'Online Order',
                                    'pos_reference' : 'Order' + ' ' +pos_data['order_serial_no'],
                                    'state': 'done' if pos_data['status_name'] == 'Delivered' else 'draft' if pos_data['status_name'] == 'Accept' else 'paid' ,
                                    'lines': line_vals
                                }
                                print(vals,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
                                self.env['pos.order'].create(vals)

            except requests.exceptions.RequestException as e:
                return {'error': str(e)}


    

    def get_floors_from_api(self, cron_mode=True):
        url = self.url + "/api/admin/dining-table?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'X-Api-Key': self.license_key or '',
        }
        existing_floor_ids = [floor.food_king_id for floor in self.env['restaurant.table'].search([])]
        food_king_floor = self.env['restaurant.floor'].search([('name', '=', 'Food King Floor')], limit=1)
        food_king_pos = self.env['pos.config'].search([('name', '=', 'Food King Pos')], limit=1)

        try:
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
                        view = self.env.ref('sh_message.sh_message_wizard')
                        context = dict(self._context or {})
                        dic_msg =  "Table Already synced ."
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
        except RequestException as e:
            self.env['ir.logging'].create({'name': 'Floor Sync', 'type': 'error', 'message': str(e)})
        except HTTPError as e:
            self.env['ir.logging'].create({'name': 'Floor Sync', 'type': 'error', 'message': f'HTTP error: {e}'})
        except Timeout as e:
            self.env['ir.logging'].create({'name': 'Floor Sync', 'type': 'error', 'message': f'Request timed out: {e}'})
        except ConnectionError as e:
            self.env['ir.logging'].create({'name': 'Floor Sync', 'type': 'error', 'message': f'Connection error: {e}'})
