from odoo import http
from odoo.http import request
import json
import hashlib
import base64

class LoginAPI(http.Controller):

    @http.route('/login123', type="http", auth="none", methods=["POST"], csrf=False)
    def login(self, model=None, id=None, **payload):
        email = payload.get('email')
        password = payload.get('password')
        print(email, password)
        if not email or not password:
            return http.Response('Email and password are required.', status=400)
        
        uid = request.session.authenticate(request.db, email, password)
        
        if not uid:
            return http.Response('Invalid credentials.', status=401)
        
        token = self.generate_token(email)
        
        return http.Response(json.dumps({'token': token}), content_type='application/json', status=200)
    
    def generate_token(self, email):
        token = hashlib.sha256(email.encode()).digest()
        return base64.b64encode(token).decode()
    
    @http.route('/api/pos_order', type='json', auth='user', methods=['POST'])
    def create_pos_order(self, **kwargs):
        print("ppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp")
        pos_session_id = kwargs.get('session_id')
        pricelist_id = kwargs.get('pricelist_id')
        partner_id = kwargs.get('partner_id')
        company_id = kwargs.get('company_id')
        lines = kwargs.get('lines', [])
        note = kwargs.get('note')
        tracking_number = kwargs.get('tracking_number')
        session_move_id = kwargs.get('session_id')
        is_accepted = kwargs.get('is_accepted')
        table_id = kwargs.get('table_id')
        status = kwargs.get('status')
        pos_reference = kwargs.get('pos_reference')
        amount_total = kwargs.get('amount_total')
        amount_tax = kwargs.get('amount_tax')
        amount_paid = kwargs.get('amount_paid')
        amount_return = kwargs.get('amount_return')
        order_ref = kwargs.get('name')
        line_vals=[]
        for line_data in lines:
            line_vals.append((0, 0, {
                            'company_id': company_id,
                            'product_id':line_data.get('product_id'),
                            'full_product_name':line_data.get('full_product_name') ,
                            'qty':line_data.get('qty'),
                            'price_unit':line_data.get('price_unit') ,
                            'discount': line_data.get('discount'),
                            'tax_ids': line_data.get('tax_ids') ,
                            'price_subtotal':line_data.get('price_subtotal_incl') ,
                            'price_subtotal_incl': line_data.get('price_subtotal_incl'),
                            'customer_note':line_data.get('customer_note')
                                                                                }))
        pos_order_vals = {
            'name':order_ref,
            'session_id': pos_session_id,
            'pricelist_id': pricelist_id,
            'partner_id': partner_id,
            'company_id': company_id,
            'note': note,
            'tracking_number': tracking_number,
            'session_move_id': session_move_id,
            'is_accepted': is_accepted,
            'table_id': table_id,
            'status': status,
            'pos_reference': pos_reference,
            'amount_total': amount_total,
            'amount_tax': amount_tax,
            'amount_paid': amount_paid,
            'amount_return': amount_return,
            'lines':line_vals
        }
        
        pos_order = request.env['pos.order'].sudo().create(pos_order_vals)
        
       
        
        
        return {'status': 'success', 'order_id': pos_order.id}