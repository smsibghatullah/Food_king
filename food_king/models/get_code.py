import requests
from odoo import models, fields, api
import json
from odoo.exceptions import AccessError,UserError
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
import re
import base64
import tempfile


def sync_all_customers(self, cron_mode=True):
           
            customers_data = self.env['res.partner'].search([])
            synced_customers = self.env['res.partner'].search([('food_king_id_res', '!=', False)]).mapped('id') 
            

            url = self.url +"/api/admin/customer"

            headers = {
               'Authorization': f'Bearer {self.auth_token}',
               'X-Api-Key':self.license_key or '',
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
                        view = self.env.ref('sh_message.sh_message_wizard')
                        context = dict(self._context or {})
                        dic_msg = response_data['message'] or 'Customer Sync Successfully'
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

            return {'message': 'New customers synced successfully.'}


# get data

    
def get_product_from_api(self, cron_mode=True):
            url = self.url + "/api/admin/item"
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                 'X-Api-Key':self.license_key or '',
            }
            existing_product_ids = [product.food_king_id for product in self.env['product.template'].search([])]

            try:
                response = requests.request("GET", url, headers=headers)
                response.raise_for_status()
                products = response.json().get('data', [])

                for product in products:
                    getcateg_id = self.env['pos.category'].search([('food_king_id', '=', product.get('item_category_id'))]).mapped('id')
                    gettax_id = self.env['account.tax'].search([('food_king_id', '=', product.get('tax_id'))]).mapped('id')
                    base64_image = self.get_base64_from_url(product.get('preview'))
                    print(product.get('name'),product.get('item_category_id'),'ssssssssssssssssssssssss')
                    vals = {
                        'name': product.get('name'),
                        'list_price': float(product.get('price')),
                        'food_king_id': product.get('id'),
                        'pos_categ_ids': getcateg_id,
                        'taxes_id': gettax_id, 
                        "food_king_active":False if product.get('status')  == 10 else True, 
                        'item_type':'veg' if product.get('item_type') == 5 else 'nonveg',
                        'is_featured':'no' if product.get('is_featured') == 10 else 'yes',
                        'description': product.get('description'),
                        'caution':product.get('caution'),
                        'image_1920':base64_image,
                        'available_in_pos' : True
                    }
                    if product.get('id') in existing_product_ids:
                        pass
                    else:
                        self.env['product.template'].create(vals)

                
                return {'message': 'Products retrieved successfully.'}
            except requests.exceptions.RequestException as e:
                return {'error': str(e)}

def get_categories_from_api(self, cron_mode=True):
            self.sync_all_category()
            url = self.url + "/api/admin/setting/item-category?paginate=1&page=1&per_page=10&order_column=id&order_type=desc"
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                 'X-Api-Key':self.license_key or '',
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
            



    
def get_tax_from_api(self, cron_mode=True):
            self.sync_all_tax()
            url = self.url + "/api/admin/setting/tax"
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                 'X-Api-Key':self.license_key or '',
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

    
    
   
    

    # def sync_all_pos_orders(self, cron_mode=True):
      

    #     orders = self.env['pos.order'].search([])
    #     synced_pos_order = self.env['pos.order'].search([('food_king_id', '!=', False)])
    #     url = self.url + "/api/admin/pos"
    #     headers = {
    #         'Authorization': f'Bearer {self.auth_token}',
    #         'X-Api-Key':self.license_key or '',
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
    

  
        