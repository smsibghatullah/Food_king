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
        Foodking_Ids = self.env['food_king.food_king'].search([('id', '=', 1)])
        synced_products = self.env['product.template'].search([('food_king_id', '=', 0)])
        url = (self.url or Foodking_Ids.url) + "/api/admin/item"
        headers = {
            'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
            'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
        }
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
                            view = self.env.ref('sh_message.sh_message_wizard')
                            context = dict(self._context or {})
                            dic_msg = (product.name + ' ' + response_data['message'])
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
                        if 'data' in response_data:
                            food_king_id = response_data['data']['id']
                            product.write({'food_king_id': food_king_id})
                            synced_product_ids.append(product.id)

                            
                    except requests.exceptions.RequestException as e:
                        print( str(e))
                        pass
        
      
        view = self.env.ref('sh_message.sh_message_wizard')
        context = dict(self._context or {})
        dic_msg = "Product Synced Successfully"
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
        Foodking_Ids = self.env['food_king.food_king'].search([('id', '=', 1)])
        self.get_admin_customer_from_api()
        url = (self.url or Foodking_Ids.url) + "/api/admin/customer"
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
  
   #  sync customer   

    def get_admin_customer_from_api(self, cron_mode=True):
        Foodking_Ids = self.env['food_king.food_king'].search([('id', '=', 1)])
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
        Foodking_Ids = self.env['food_king.food_king'].search([('id', '=', 1)])
        synced_categories = self.env['pos.category'].search([('food_king_id', '=', 0)])
        url = (self.url or Foodking_Ids.url) + "/api/admin/setting/item-category?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
        headers = {
            'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
            'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
            # 'Content-Type': 'application/json',
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
                            view = self.env.ref('sh_message.sh_message_wizard')
                            context = dict(self._context or {})
                            dic_msg = (category.name + ' ' + response_data['message'])
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
                if 'data' in response_data:
                    food_king_id = response_data['data']['id']
                    category.write({'food_king_id': food_king_id})
                    synced_categories_ids.append(category.id)
            except requests.exceptions.RequestException as e:
                        print( str(e))
                        pass

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

   #  sync all taxes          # 
     
    def sync_all_tax(self, cron_mode=True):
            Foodking_Ids = self.env['food_king.food_king'].search([('id', '=', 1)])
            taxes = self.env['account.tax'].search([])
            synced_taxes = self.env['account.tax'].search([('food_king_id', '=', 0)])
            url = (self.url or Foodking_Ids.url) + "/api/admin/setting/tax"
            headers = {
                'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
                'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
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
                        print(response_data,'llllllllllllllllllllll')
                        if 'message' in response_data:
                            view = self.env.ref('sh_message.sh_message_wizard')
                            context = dict(self._context or {})
                            dic_msg = (tax.name + ' ' + response_data['message'])
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
                        if 'data' in response_data:
                            food_king_id = response_data['data']['id']
                            tax.write({'food_king_id': food_king_id})
                            synced_tax_ids.append(tax.id)
                     
                        

                    except requests.exceptions.RequestException as e:
                         print( str(e))
                         pass
        
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
    
   #  sync pos order

    def get_pos_order_from_api(self, cron_mode=True):
            success_true = False
            self.get_online_order_from_api()
            Foodking_Ids = self.env['food_king.food_king'].search([('id', '=', 1)])
            url = f"{self.url or Foodking_Ids.url}/api/admin/table-order?paginate=1&page=1&per_page=10&order_column=id&order_by=desc&order_type=20"
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
                        data_filter_by_branch = self.company_id.branch_id.food_king_id
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
                                        if product_Variants_ids:
                                            for item_id in product_Variants_ids:
                                                    for itemdata in item_id['product_template_variant_value_ids']:
                                                        print(variation_ids)
                                                        if itemdata.food_king_id in variation_ids:
                                                            print(item_id.id,item_id.name,"oooooooooooooooooooooooooooooooooooooooooo")
                                                            line_vals.append((0, 0, {
                                                                'uuid': uid_counter,
                                                                'company_id': self.company_id.id,
                                                                'product_id': item_id.id,
                                                                'full_product_name': full_product_name,
                                                                'qty': posid['quantity'],
                                                                'price_unit': float(price),
                                                                'discount': float(discount),
                                                                'tax_ids': [(6, 0, [int(product_tax)])] if product_tax else False,
                                                                'price_subtotal': float(posid['total_convert_price']) - (float(posid['total_convert_price']) * float(product_tax.amount) if product_tax else 0) / 100 if product_tax.price_include else float(posid['total_convert_price']),
                                                                'price_subtotal_incl': float(posid['total_convert_price'])  if product_tax.price_include else float(posid['total_convert_price']) + (float(posid['total_convert_price']) * float(product_tax.amount) if product_tax else 0) / 100
                                                            }))
                                                            uid_counter += 1
                                                    if posid['item_variations'] == [] :
                                                        line_vals.append((0, 0, {
                                                                            'company_id': self.company_id.id,
                                                                            'product_id': item_id.id,
                                                                            'full_product_name': full_product_name,
                                                                            'qty': posid['quantity'],
                                                                            'price_unit': float(price),
                                                                            'discount': float(discount),
                                                                            'tax_ids': [(6, 0, [int(product_tax)])] if product_tax else None,
                                                                            'price_subtotal': float(posid['total_convert_price']) - (float(posid['total_convert_price']) * float(product_tax.amount) if product_tax else 0) / 100 if product_tax.price_include else float(posid['total_convert_price']),
                                                                            'price_subtotal_incl': float(posid['total_convert_price'])  if product_tax.price_include else float(posid['total_convert_price']) + (float(posid['total_convert_price']) * float(product_tax.amount) if product_tax else 0) / 100
                                                                        }))

                                if customer_ids:
                                    # search_pos = self.env['pos.config'].search([('name', '=', 'Food King Pos')]).mapped('id')
                                    search_table = self.env['restaurant.table'].search([('name', '=',pos_data['table_name'] )]).mapped('id')
                                    customer_id = customer_ids[0]
                                    # if search_pos:
                                    table_id = 0
                                    config_id = self.point_of_sale.id
                                    if search_table:
                                        table_id = search_table[0]
                                    total_tax_currency_price = re.sub(r'[^\d.]+', '', pos_data['total_tax_currency_price'])
                                    subtotal_currency_price = re.sub(r'[^\d.]+', '', pos_data['subtotal_currency_price'])
                                    search_pos_session = self.env['pos.session'].sudo().search([('state', '=', 'opened')])
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
                                                'company_id': self.company_id.id,
                                                'amount_tax':  float(total_tax_currency_price),
                                                'amount_paid': float(subtotal_currency_price),
                                                'amount_return': 0.0,
                                                'table_id':table_id,
                                                'status':'Table Order',
                                                'pos_reference' : result,
                                                'state': 'done' if pos_data['status_name'] == 'Delivered'  else 'paid' if pos_data['payment_status'] == 5 else 'draft'  ,
                                                'lines': line_vals,
                                                'note':'\n'.join(instruction)
                                            }
                                            self.env['pos.order'].sudo().create(vals)
                                            self.send_message_to_food_king_users(f"New order. Order ID: {result}")
                                            success_true = True
                       
                                        else :
                                            raise UserError(('Please open the session'))
                                        
                                    else :
                                        raise UserError(('Please select point of sale'))
                   
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
               
            

            except requests.exceptions.RequestException as e:
                return {'error': str(e)}
  
   #  sync online order

    def get_online_order_from_api(self, cron_mode=True):
            
            Foodking_Ids = self.env['food_king.food_king'].sudo().search([('id', '=', 1)])
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
                        data_filter_by_branch = self.company_id.branch_id.food_king_id
                        if data_filter_by_branch == pos_data1['branch_id']:
                            print('mubeen 1')
                            url_get_id = f"{self.url or Foodking_Ids.url}/api/admin/online-order/show/{pos_data1['id']}"
                            response_get_id = requests.get(url_get_id, headers=headers)
                            pos_data = response_get_id.json().get('data', {})
                            print(pos_data,"qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq")
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
                                    variation_names = [variation['name'] for variation in posid['item_variations']]
                                    full_product_name = product_name+' (' +','.join(variation_names)+')' if variation_names else product_name
                                    instruction.append(full_product_name + ' : ' + posid['instruction'])
                                    uid_counter = 1
                                    variation_ids = [variation['id'] for variation in posid['item_variations']]
                                    print(product_Variants_ids,variation_names,variation_ids,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
                                    if product_Variants_ids:
                                        print('ddddddddddddddddddddddddddddddddddddddddddddddd')
                                        for item_id in product_Variants_ids:
                                                print(item_id['product_template_variant_value_ids'],"cccccccccccccccccccccccccccccccccccccccccccccccccccccc")
                                                # for itemdata in item_id['product_template_variant_value_ids']:
                                                print("jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj")
                                                    # if itemdata.food_king_id in variation_ids:
                                                print(item_id.id,item_id.name,"oooooooooooooooooooooooooooooooooooooooooo")
                                                line_vals.append((0, 0, {
                                                    'uuid': uid_counter,
                                                    'company_id': self.company_id.id,
                                                    'product_id': item_id.id,
                                                    'full_product_name': full_product_name,
                                                    'qty': posid['quantity'],
                                                    'price_unit': float(price),
                                                    'discount': float(discount),
                                                    'tax_ids': [(6, 0, [int(product_tax)])] if product_tax else None,
                                                    'price_subtotal': float(posid['total_convert_price']) - (float(posid['total_convert_price']) * float(product_tax.amount) if product_tax else 0) / 100 if product_tax.price_include else float(posid['total_convert_price']),
                                                    'price_subtotal_incl': float(posid['total_convert_price'])  if product_tax.price_include else float(posid['total_convert_price']) + (float(posid['total_convert_price']) * float(product_tax.amount) if product_tax else 0) / 100
                                                }))
                                                uid_counter += 1
                                                if posid['item_variations'] == [] :
                                                    line_vals.append((0, 0, {
                                                                        'company_id': self.company_id.id,
                                                                        'product_id': item_id.id,
                                                                        'full_product_name': full_product_name,
                                                                        'qty': posid['quantity'],
                                                                        'price_unit': float(price),
                                                                        'discount': float(discount),
                                                                        'tax_ids': [(6, 0, [int(product_tax)])] if product_tax else None,
                                                                        'price_subtotal': float(posid['total_convert_price']) - (float(posid['total_convert_price']) * float(product_tax.amount) if product_tax else 0) / 100 if product_tax.price_include else float(posid['total_convert_price']),
                                                                        'price_subtotal_incl': float(posid['total_convert_price'])  if product_tax.price_include else float(posid['total_convert_price']) + (float(posid['total_convert_price']) * float(product_tax.amount) if product_tax else 0) / 100
                                                                    }))
                                         
                            if customer_ids:
                                customer_id = customer_ids[0]
                                table_id = 0
                                config_id = self.point_of_sale.id
                                total_tax_currency_price = re.sub(r'[^\d.]+', '', pos_data['total_tax_currency_price'])
                                total_currency_price = re.sub(r'[^\d.]+', '', pos_data['total_currency_price'])
                                delivery_charges =  self.env['product.product'].search([('name', '=', 'Delivery Charge')])
                                delivery_charge_currency_price = re.sub(r'[^\d.]+', '', pos_data['delivery_charge_currency_price'])
                                line_vals.append((0, 0, {
                                    'product_id': delivery_charges.id,
                                    'full_product_name': delivery_charges.name,
                                    'qty': 1,
                                    'company_id': self.company_id.id,
                                    'price_unit': float(delivery_charge_currency_price),
                                    'tax_ids' : [(4, delivery_charges.taxes_id.id)] if delivery_charges != '' else None,
                                    'price_subtotal': float(delivery_charge_currency_price) - (float(delivery_charge_currency_price) * delivery_charges.taxes_id.amount) / 100 if delivery_charges.taxes_id.price_include else float(delivery_charge_currency_price) ,
                                    'price_subtotal_incl':float(delivery_charge_currency_price) if delivery_charges.taxes_id.price_include else float(delivery_charge_currency_price) + (float(delivery_charge_currency_price) * delivery_charges.taxes_id.amount) / 100
                                }))
                                search_pos_session = self.env['pos.session'].sudo().search([
                                    ('state', '=', 'opened'), 
                                    ('company_id', '=', self.company_id.id),
                                    ('config_id', '=', self.point_of_sale.id)
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
                                                'amount_total': sum([line[2]['price_subtotal_incl'] for line in line_vals]),
                                                'session_id': search_pos_session[0].id,
                                                'company_id': self.company_id.id,
                                                'amount_tax':  float(total_tax_currency_price),
                                                'amount_paid': sum([line[2]['price_subtotal_incl'] for line in line_vals]) if pos_data['payment_status'] == 5 else 0,
                                                'amount_return': 0.0,
                                                'table_id':table_id,
                                                'status':'Online Order',
                                                'pos_reference' : result,
                                                'state': 'done' if pos_data['status_name'] == 'Delivered'  else 'paid' if pos_data['payment_status'] == 5 else 'draft'  ,
                                                'lines': line_vals,
                                                'note':'\n'.join(instruction),
                                                'tracking_number':803,
                                                'session_move_id':7
                                            }
                                            print(instruction,vals,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
                                            # self.env['pos.order'].sudo().create(vals)
                                            self.send_message_to_food_king_users(f"New order. Order ID: {result}")
                                        
                                    else :
                                        raise UserError(('Please open the session'))
                                        
                                else :
                                      raise UserError(('Please select point of sale'))

            except requests.exceptions.RequestException as e:
                return {'error': str(e)}
  
   #  sync floor

    def get_floors_from_api(self, cron_mode=True):
        Foodking_Ids = self.env['food_king.food_king'].search([('id', '=', 1)])
        url = (self.url or Foodking_Ids.url) + "/api/admin/dining-table?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
        headers = {
            'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
            'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
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
  
   #  sync branch

    def get_branch_from_api(self, cron_mode=True):
        Foodking_Ids = self.env['food_king.food_king'].search([('id', '=', 1)])
        url = (self.url or Foodking_Ids.url) + "/api/admin/setting/branch?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
        headers = {
            'Authorization': f'Bearer {self.auth_token or Foodking_Ids.auth_token}',
            'X-Api-Key':self.license_key or '' or Foodking_Ids.license_key,
        }
        existing_branch_ids = [branch.food_king_id for branch in self.env['food.king.branch'].search([])]

        try:
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

        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
   
   # Sync Message
    def send_message_to_food_king_users(self, message_body):
        group = self.env.ref('food_king.group_food_king_user')
        users = self.env['res.users'].search([('groups_id', 'in', [group.id])])

        administrator = self.env.user.partner_id

        for user in users:
            message = self.env['mail.message'].create({
                'author_id': administrator.id,
                'model': 'discuss.channel',
                'res_id': 1,
                'message_type': 'comment',
                'body': message_body,
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'record_name': "Food King Message",
            })

        

            