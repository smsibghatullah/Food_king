import requests
from odoo import models, fields, api
import json
from odoo.exceptions import AccessError,UserError

class FoodKingTokenWizard(models.TransientModel):
    _name = 'food_king.token.wizard'
    _description = 'Success'

    message = fields.Text('Message', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(FoodKingTokenWizard, self).default_get(fields)
        res['message'] = self.env.context.get('default_message', '')
        return res

    def action_close_wizard(self):
        return {'type': 'ir.actions.act_window_close'}
class food_king(models.Model):
    _name = 'food_king.food_king'

    username = fields.Char('Username')
    password = fields.Char('Password', widget='password')
    url = fields.Char('URL')
    auth_token = fields.Char('Token')


    def get_token(self):
        login_url = self.url + "/api/auth/login"
        headers = {
            'Content-Type': 'application/json',
             'Authorization': '',
             'X-Api-Key':'z6m74ch3-c9o8-61x8-8437-p625q35566f139720'
        }
        print(self.username)
        login_payload = {
            "email": self.username,
            "password": self.password
        }

        try:
            response = requests.post(login_url, headers=headers, json=login_payload)
            response_data = response.json()
            token = response_data['token']
            if not token:
                return {'error': 'Failed to obtain access token.'}
            self.auth_token = token
            message = response_data.get('message') if response_data.get('message') else response_data
            return {
                'name': 'Action',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'food_king.token.wizard',
                'target': 'new',
                'context': {'default_message': message},
            }
            return token
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
        

    def sync_all_products(self, cron_mode=True):
        message_data=''
        products = self.env['product.template'].search([])
        synced_products = self.env['product.template'].search([('food_king_id', '!=', False)]).mapped('id')
        url = self.url + "/api/admin/item"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'X-Api-Key':'z6m74ch3-c9o8-61x8-8437-p625q35566f139720',
            'Content-Type': 'application/json',
        }
        for product in products:
            if product.id not in synced_products:
                if product.pos_categ_ids:
                    food_king_id = product.pos_categ_ids[0].food_king_id
                    food_king_id_tax = product.taxes_id.food_king_id
                    payload = json.dumps({
                        "name": product.name,
                        "price": product.list_price,
                        "item_category_id": food_king_id,
                        "tax_id": food_king_id_tax,
                        "item_type":product.item_type ,
                        "is_featured": product.is_featured,
                        "description": product.description,
                        "caution": product.caution,
                        "order": product.sequence,
                        "status": 5
                    })

                    try:
                        response = requests.post(url, headers=headers, data=payload)
                        response_data = response.json()
                        message_data = response_data.get('message') if response_data.get('message') else response_data
                        if 'data' in response_data:
                            print('ooooooooooooooo')
                            food_king_id = response_data['data']['id']
                            product.write({'food_king_id': food_king_id})


                    except requests.exceptions.RequestException as e:
                        return {'error': str(e)}
        message = message_data
        print(message,'ffffffffffffffffffffffffff')
        return {
            'name': 'Action',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'food_king.token.wizard',
            'target': 'new',
            'context': {'default_message': message},
        }
        return {'message': 'New products synced successfully.'}
    
    def get_product_from_api(self, cron_mode=True):
            self.sync_all_products()
            url = self.url + "/api/admin/item"
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'X-Api-Key':'z6m74ch3-c9o8-61x8-8437-p625q35566f139720',
            }
            existing_product_ids = [product.food_king_id for product in self.env['product.template'].search([])]

            try:
                response = requests.request("GET", url, headers=headers)
                response.raise_for_status()
                products = response.json().get('data', [])

                for product in products:
                    vals = {
                        'name': product.get('name'),
                        'list_price': float(product.get('price')),
                        'food_king_id': product.get('id'),
                        # 'item_category_id': food_king_id,  
                        # 'tax_id': food_king_id_tax,  
                        'item_type':'veg' if product.get('item_type') == 5 else 'nonveg',
                        'is_featured':'no' if product.get('is_featured') == 10 else 'yes',
                        'description': product.get('description'),
                        'caution':product.get('caution'),
                    }
                    if product.get('id') in existing_product_ids:
                        pass
                    else:
                        self.env['product.template'].create(vals)

                
                return {'message': 'Products retrieved successfully.'}
            except requests.exceptions.RequestException as e:
                return {'error': str(e)}

    def sync_all_category(self, cron_mode=True):
         
        categories = self.env['pos.category'].search([])
        synced_categories = self.env['pos.category'].search([('food_king_id', '!=', False)]).mapped('id')
        url = self.url + "/api/admin/setting/item-category?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'X-Api-Key':'z6m74ch3-c9o8-61x8-8437-p625q35566f139720',
            'Content-Type': 'application/json',
        }
        for category in categories:
            if category.id not in synced_categories:
                payload = json.dumps({
                    "name": category.name,
                    "status": 5,
                    "description": category.name
                })

                try:
                    response = requests.post(url, headers=headers, data=payload)
                    response_data = response.json()
                    if 'data' in response_data:
                        food_king_id = response_data['data']['id']
                        category.write({'food_king_id': food_king_id})
                    message = response_data.get('message') if response_data.get('message') else response_data
                    print(message,'ffffffffffffffffffffffffff')
                    return {
                        'name': 'Action',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'food_king.token.wizard',
                        'target': 'new',
                        'context': {'default_message': message},
                    }
                except requests.exceptions.RequestException as e:
                    return {'error': str(e)}
       
        return {'message': 'New categories synced successfully.'}
    
    def get_categories_from_api(self, cron_mode=True):
            self.sync_all_category()
            url = self.url + "/api/admin/setting/item-category?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'X-Api-Key':'z6m74ch3-c9o8-61x8-8437-p625q35566f139720',
            }
            existing_category_ids = [categ.food_king_id for categ in self.env['pos.category'].search([])]

            try:
                response = requests.request("GET", url, headers=headers)
                response.raise_for_status()
                categories = response.json().get('data', [])

                for category in categories:
                    vals = {
                        'name': category.get('name'),
                        'food_king_id': category.get('id'),
                    }
                    if category.get('id') in existing_category_ids:
                        pass
                    else:
                        self.env['pos.category'].create(vals)

                
                return {'message': 'Categories retrieved successfully.'}
            except requests.exceptions.RequestException as e:
                return {'error': str(e)}

    def sync_all_tax(self, cron_mode=True):
            taxes = self.env['account.tax'].search([])
            synced_taxes = self.env['account.tax'].search([('food_king_id', '!=', False)]).mapped('id')
            url = self.url + "/api/admin/setting/tax"
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'X-Api-Key':'z6m74ch3-c9o8-61x8-8437-p625q35566f139720',
                'Content-Type': 'application/json',
            }
            for tax in taxes:
                if tax.id not in synced_taxes:
                    payload = json.dumps({
                        "name": tax.name,
                        "code": tax.name,
                        "tax_rate": tax.amount,
                        "status": 5
                    })

                    try:
                        response = requests.post(url, headers=headers, data=payload)
                        response_data = response.json()
                        if 'data' in response_data:
                            food_king_id = response_data['data']['id']
                            tax.write({'food_king_id': food_king_id})
                            message = response_data.get('message') if response_data.get('message') else response_data
                            print(message,'ffffffffffffffffffffffffff')
                            return {
                                'name': 'Action',
                                'type': 'ir.actions.act_window',
                                'view_mode': 'form',
                                'res_model': 'food_king.token.wizard',
                                'target': 'new',
                                'context': {'default_message': message},
                            }                        
                    except requests.exceptions.RequestException as e:
                        return {'error': str(e)}

            return {'message': 'New taxes synced successfully.'}
    
    def get_tax_from_api(self, cron_mode=True):
            self.sync_all_tax()
            url = self.url + "/api/admin/setting/tax"
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'X-Api-Key':'z6m74ch3-c9o8-61x8-8437-p625q35566f139720',
            }
            existing_tax_ids = [tax.food_king_id for tax in self.env['account.tax'].search([])]

            try:
                response = requests.request("GET", url, headers=headers)
                response.raise_for_status()
                taxes = response.json().get('data', [])

                for tax in taxes:
                    vals = {
                        'name': tax.get('name'),
                        'food_king_id': tax.get('id'),
                        'amount':tax.get('tax_rate')
                    }
                    if tax.get('id') in existing_tax_ids:
                        pass
                    else:
                        self.env['account.tax'].create(vals)

                
                return {'message': 'Taxes retrieved successfully.'}
            except requests.exceptions.RequestException as e:
                return {'error': str(e)}

    def sync_all_customers(self, cron_mode=True):
           
            customers_data = self.env['res.partner'].search([])
            synced_customers = self.env['res.partner'].search([('food_king_id_res', '!=', False)]).mapped('id') 
            

            url = self.url +"/api/admin/customer"

            headers = {
               'Authorization': f'Bearer {self.auth_token}',
               'X-Api-Key':'z6m74ch3-c9o8-61x8-8437-p625q35566f139720',
               'Content-Type': 'application/json',
            }
            
            for customer in customers_data:
                if customer.id not in synced_customers: 
                    payload = {
                        "name": customer.name,
                        "email": customer.email,
                        "phone": customer.phone,
                        "password": "123456",
                        "password_confirmation": "123456",
                        "country_code": customer.country_id.code,
                        "status": 5
                    }

                    try:
                        response = requests.post(url, headers=headers, json=payload)
                        response_data = response.json()
                        if 'data' in response_data:
                            food_king_id = response_data['data']['id'] 
                            customer.write({'food_king_id_res': food_king_id})
                            message = response_data.get('message') if response_data.get('message') else response_data
                            return {
                                'name': 'Action',
                                'type': 'ir.actions.act_window',
                                'view_mode': 'form',
                                'res_model': 'food_king.token.wizard',
                                'target': 'new',
                                'context': {'default_message': message},
                            }
                    except requests.exceptions.RequestException as e:
                        return {'error': str(e)}

            return {'message': 'New customers synced successfully.'}
    
    def get_customer_from_api(self, cron_mode=True):
            self.sync_all_customers()
            url = self.url + "/api/admin/customer"
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'X-Api-Key':'z6m74ch3-c9o8-61x8-8437-p625q35566f139720',
            }
            existing_customer_ids = [customer.food_king_id_res for customer in self.env['res.partner'].search([])]

            try:
                response = requests.request("GET", url, headers=headers)
                response.raise_for_status()
                customers = response.json().get('data', [])

                for customer in customers:
                    vals = {
                       "name": customer.get('name'),
                       "email":customer.get('email'),
                       "phone":customer.get('phone'),
                       'food_king_id_res': customer.get('id'),
                    }
                    if customer.get('id') in existing_customer_ids:
                        pass
                    else:
                        self.env['res.partner'].create(vals)

                
                return {'message': 'Customers retrieved successfully.'}
            except requests.exceptions.RequestException as e:
                return {'error': str(e)}
    

    # def sync_all_pos_orders(self, cron_mode=True):
      

    #     orders = self.env['pos.order'].search([])
    #     synced_pos_order = self.env['pos.order'].search([('food_king_id', '!=', False)])
    #     url = self.url + "/api/admin/pos"
    #     headers = {
    #         'Authorization': f'Bearer {self.auth_token}',
    #         'X-Api-Key':'z6m74ch3-c9o8-61x8-8437-p625q35566f139720',
    #         'Content-Type': 'application/json',
    #     }

    #     for order in orders:
    #         if order.name not in synced_pos_order:
    #             items = []
    #             for line in order.lines:
    #                 item = {
    #                     "item_id": line.product_id.food_king_id if line.product_id.food_king_id else line.product_id.food_king_id,
    #                     "item_price": line.price_unit,
    #                     "branch_id": 1,  
    #                     "instruction": "",
    #                     "quantity": line.qty,
    #                     "discount": line.discount,
    #                     "total_price": line.price_subtotal,
    #                     "item_variation_total": 0,
    #                     "item_extra_total": 0,
    #                     "item_variations": [],
    #                     "item_extras": []
    #                 }
    #                 items.append(item)

    #             payload = {
    #                 "branch_id": 1, 
    #                 "subtotal": order.amount_total,
    #                 "token": "",
    #                 "customer_id": order.partner_id.food_king_id_res if order.partner_id.food_king_id_res else order.partner_id.food_king_id_res,
    #                 "discount": 0,
    #                 "delivery_charge": 0,  
    #                 "delivery_time": None, 
    #                 "total": order.amount_total,
    #                 "order_type": 15,  
    #                 "is_advance_order": 10,  
    #                 "source": 15,  
    #                 "address_id": None,  
    #                 "coupon_id": None,  
    #                 "items": str(items).replace("'", "\"")  
    #             }

    #         try:
    #             response = requests.request("POST", url, headers=headers, json=payload)
    #             response_data = response.json()
    #             print(response_data,'pooooooooooooooooooooooooooooooooo')
    #             if 'data' in response_data:
    #                 food_king_id = response_data['data']['id']
    #                 order.write({'food_king_id': food_king_id})

    #         except requests.exceptions.RequestException as e:
    #             return {'error': str(e)}

    #     return {'message': 'All POS orders synced successfully.'}
    

    def get_pos_order_from_api(self, cron_mode=True):
        url = f"{self.url}/api/admin/pos-order?paginate=1&page=1&per_page=10&order_column=id&order_by=desc&order_type=15"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'X-Api-Key':'z6m74ch3-c9o8-61x8-8437-p625q35566f139720',
        }

        existing_pos_order_ids = [pos.food_king_id for pos in self.env['pos.order'].search([])]

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            pos_orders = response.json().get('data', [])

            for pos_data in pos_orders:
                url_get_id = f"{self.url}/api/admin/pos-order/show/{pos_data['id']}"
                response_get_id = requests.get(url_get_id, headers=headers)
                pos_data = response_get_id.json().get('data', {})
                print(pos_data,"mubeenawannnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn")
                customer_ids = self.env['res.partner'].search([('food_king_id_res', '=', pos_data.get('user', {}).get('id'))]).mapped('id')

                line_vals = []
                for posid in pos_data.get('order_items', []):
                    product_ids = self.env['product.template'].search([('food_king_id', '=', posid.get('item_id'))]).mapped('id')
                    products_name = self.env['product.template'].search([('food_king_id', '=', posid.get('item_id'))]).mapped('name')
                    if product_ids or products_name:
                        product_id = product_ids[0]
                        product_name = products_name[0]

                        line_vals.append((0, 0, {
                            'product_id': product_id,
                            'full_product_name': product_name,
                            'qty': posid.get('quantity'),
                            'price_unit': posid.get('price'),
                            'discount': posid.get('discount'),
                            'price_subtotal': posid.get('total_convert_price'),
                            'price_subtotal_incl': posid.get('total_convert_price')
                        }))
                print(line_vals,"vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv")
                if customer_ids:
                    customer_id = customer_ids[0]

                    vals = {
                        'name': pos_data.get('order_serial_no'),
                        'partner_id': customer_id,
                        'amount_total': pos_data.get('subtotal_currency_price'),
                        'session_id': pos_data.get('branch', {}).get('id'),
                        'company_id': pos_data.get('branch', {}).get('id'),
                        'amount_tax': pos_data.get('total_tax_currency_price'),
                        'amount_paid': pos_data.get('subtotal_currency_price'),
                        'amount_return': 0,
                        'lines': line_vals
                    }

                    if pos_data.get('id') in existing_pos_order_ids:
                        print('gggggggggggggggggggggggggggggggggggggSSSSS')
                        pass
                    else:
                        print(vals,"kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk")
                        self.env['pos.order'].create(vals)

            return {'message': 'Pos order retrieved successfully.'}

        except requests.exceptions.RequestException as e:
            return {'error': str(e)}



            









       