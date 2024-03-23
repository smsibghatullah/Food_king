import requests
from odoo import models, fields, api
import json

class food_king(models.Model):
    _name = 'food_king.food_king'

    username = fields.Char('Username')
    password = fields.Char('Password')
    url = fields.Char('URL')


    def get_token(self):
        login_url = self.url + "/api/auth/login"
        headers = {
            'Content-Type': 'application/json',
             'Authorization': '',
             'X-Api-Key':''
        }
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
            return token
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

    def sync_all_products(self, cron_mode=True):
        token = self.get_token()
        print(token,"pppppppppppppppppppppppppppppp")
        if 'error' in token:
            return token

        products = self.env['product.template'].search([])
        synced_products = self.env['product.template'].search([('food_king_id', '!=', False)]).mapped('name')
        url = self.url + "/api/admin/item"
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Api-Key':'',
            'Content-Type': 'application/json',
        }

        for product in products:
            if product.name not in synced_products:
                if product.pos_categ_ids:
                    food_king_id = product.pos_categ_ids[0].food_king_id
                    food_king_id_tax = product.taxes_id.food_king_id
                    payload = json.dumps({
                        "name": product.name,
                        "price": product.list_price,
                        "item_category_id": food_king_id,
                        "tax_id": food_king_id_tax,
                        "item_type": 7,
                        "is_featured": 5,
                        "description": product.detailed_type,
                        "caution": product.detailed_type,
                        "order": product.sequence,
                        "status": 5
                    })

                    try:
                        response = requests.post(url, headers=headers, data=payload)
                        response_data = response.json()
                        if 'data' in response_data:
                            food_king_id = response_data['data']['id']
                            product.write({'food_king_id': food_king_id})

                    except requests.exceptions.RequestException as e:
                        return {'error': str(e)}

        return {'message': 'New products synced successfully.'}

    def sync_all_category(self, cron_mode=True):
        token = self.get_token()
        if 'error' in token:
            return token

        categories = self.env['pos.category'].search([])
        synced_categories = self.env['pos.category'].search([('food_king_id', '!=', False)]).mapped('name')
        url = self.url + "/api/admin/setting/item-category?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Api-Key':'',
            'Content-Type': 'application/json',
        }

        for category in categories:
            if category.name not in synced_categories:
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

                except requests.exceptions.RequestException as e:
                    return {'error': str(e)}

        return {'message': 'New categories synced successfully.'}

    def sync_all_tax(self, cron_mode=True):
        token = self.get_token()
        if 'error' in token:
            return token

        taxes = self.env['account.tax'].search([])
        synced_taxes = self.env['account.tax'].search([('food_king_id', '!=', False)]).mapped('name')
        url = self.url + "/api/admin/setting/tax"
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Api-Key':'',
            'Content-Type': 'application/json',
        }

        for tax in taxes:
            if tax.name not in synced_taxes:
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

                except requests.exceptions.RequestException as e:
                    return {'error': str(e)}

        return {'message': 'New taxes synced successfully.'}

    def sync_all_customers(self, cron_mode=True):
            token = self.get_token()
            if 'error' in token:
                     return token
            synced_emails = set() 
            existing_customers = self.env['res.partner'].search([('food_king_id_res', '!=', False)])
            
            for customer in existing_customers:
                synced_emails.add(customer.email)  

            url = self.url +"/api/admin/customer"

            headers = {
               'Authorization': f'Bearer {token}',
               'X-Api-Key':'',
               'Content-Type': 'application/json',
            }

            new_customers = self.env['res.partner'].search([('food_king_id_res', '=', False)])  
            
            for customer in new_customers:
                if customer.email not in synced_emails: 
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
                        print(response_data,'kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
                        if 'data' in response_data:
                            food_king_id = response_data['data']['id'] 
                            customer.write({'food_king_id_res': food_king_id})
                    
                    except requests.exceptions.RequestException as e:
                        return {'error': str(e)}

            return {'message': 'New customers synced successfully.'}
    

    def sync_all_pos_orders(self, cron_mode=True):
        token = self.get_token()
        if 'error' in token:
            return token

        orders = self.env['pos.order'].search([])
        synced_pos_order = self.env['pos.order'].search([('food_king_id', '!=', False)])
        url = self.url + "/api/admin/pos"
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Api-Key':'',
            'Content-Type': 'application/json',
        }

        for order in orders:
            if order.name not in synced_pos_order:
                items = []
                for line in order.lines:
                    print(line.product_id.food_king_id,'nnnnnnnnnnnnnnnnnnnnnnnnnnnn')
                    item = {
                        "item_id": line.product_id.food_king_id if line.product_id.food_king_id else line.product_id.food_king_id,
                        "item_price": line.price_unit,
                        "branch_id": 1,  
                        "instruction": "",
                        "quantity": line.qty,
                        "discount": line.discount,
                        "total_price": line.price_subtotal,
                        "item_variation_total": 0,
                        "item_extra_total": 0,
                        "item_variations": [],
                        "item_extras": []
                    }
                    items.append(item)
                    print(items,"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")

                payload = {
                    "branch_id": 1, 
                    "subtotal": order.amount_total,
                    "token": "",
                    "customer_id": order.partner_id.food_king_id_res if order.partner_id.food_king_id_res else order.partner_id.food_king_id_res,
                    "discount": 0,
                    "delivery_charge": 0,  
                    "delivery_time": None, 
                    "total": order.amount_total,
                    "order_type": 15,  
                    "is_advance_order": 10,  
                    "source": 15,  
                    "address_id": None,  
                    "coupon_id": None,  
                    "items": str(items).replace("'", "\"")  
                }

            try:
                response = requests.request("POST", url, headers=headers, json=payload)
                response_data = response.json()
                print(response_data,'kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk')
                if 'data' in response_data:
                    food_king_id = response_data['data']['id']
                    order.write({'food_king_id': food_king_id})

            except requests.exceptions.RequestException as e:
                return {'error': str(e)}

        return {'message': 'All POS orders synced successfully.'}



            









       