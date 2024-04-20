from odoo import api, fields, models, _


class ProductProduct(models.Model):
	_inherit = 'product.product'

	is_topping = fields.Boolean(string="Is Topping")
	topping_group_ids = fields.Many2many("topping.groups",string="Topping Groups")
	topping_ids = fields.Many2many("product.product",'rel_prod_prod_db','p1','p2',string="Toppings",domain=[("is_topping","=",True)])

	@api.onchange('topping_group_ids')
	def onchange_topping_group_ids(self):
		self.topping_ids = [(6,0,self.topping_group_ids.topping_ids.ids)]
		

class ToppingGroups(models.Model):
	_name = 'topping.groups'
	_description = "Topping Groups"

	name = fields.Char('Name', required=True)
	topping_ids = fields.Many2many("product.product",'rel_prod_tg_db','tg_id','prod_id',string="Toppings",domain=[("is_topping","=",True)])


class PosCategory(models.Model):
	_inherit = 'pos.category'

	topping_ids = fields.Many2many("product.product",'rel_prod_categ_db','categ_id','prod_id',string="Toppings",domain=[("is_topping","=",True)])


class PosConfig(models.Model):
	_inherit = 'pos.config'

	activate_toppings = fields.Boolean('Enable Product Toppings')
	add_topping_default = fields.Boolean('Add toppings on product add')


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	activate_toppings = fields.Boolean(related='pos_config_id.activate_toppings',readonly=False)
	add_topping_default = fields.Boolean(related='pos_config_id.add_topping_default',readonly=False)


class pos_order(models.Model):
	_inherit = 'pos.order'

	@api.model
	def _process_order(self, order, draft, existing_order):
		odr = order['data']
		new_lines = []
		for lines in odr['lines']:
			toppingdata = lines[2].get('toppingdata',False)
			combo_list = []
			for product in toppingdata:
				vals =  [0, 0, {
					'qty': product.get('qty',1),
					'price_unit': 0,
					'price_subtotal': 0,
					'price_subtotal_incl': 0,
					'discount': 0,
					'product_id': product.get('id',False),
					'tax_ids': [[6, False, []]],
					'full_product_name': product.get('name',"-"),
					'name': product.get('name',"-"),
				}]
				new_lines.append(vals)
		# order['data']['lines'].extend(new_lines)
		return super(pos_order, self)._process_order(order, draft, existing_order)


class POSSession(models.Model):
	_inherit = 'pos.session'

	def _pos_ui_models_to_load(self):
		result = super()._pos_ui_models_to_load()
		result.extend(['topping.groups'])
		return result

	def _loader_params_topping_groups(self):
		return {
			'search_params': {
				'domain': [], 
				'fields': ['name','id','topping_ids'],
			}
		}

	def _get_pos_ui_topping_groups(self, params):
		return self.env['topping.groups'].search_read(**params['search_params'])

	def _loader_params_product_product(self):
		res = super(POSSession, self)._loader_params_product_product()
		fields = res.get('search_params').get('fields')
		fields.extend(['is_topping','topping_group_ids','topping_ids'])
		res['search_params']['fields'] = fields
		return res

	def _loader_params_pos_category(self):
		res = super(POSSession, self)._loader_params_pos_category()
		fields = res.get('search_params').get('fields')
		fields.extend(['topping_ids'])
		res['search_params']['fields'] = fields
		return res

	def _pos_data_process(self, loaded_data):
		super()._pos_data_process(loaded_data)

		loaded_data['topping_group_by_id'] = {ppp['id']: ppp for ppp in loaded_data['topping.groups']}
		topping_prods = {}
		for prods in loaded_data['product.product']:
			if prods.get('is_topping',False) :
				topping_prods.update({
					prods['id']: prods
				})
		loaded_data['toppings_by_id'] = topping_prods


class pos_order_line(models.Model):
	_inherit = 'pos.order.line'

	line_topping_ids = fields.Many2many("product.product",string="Product Toppings")


	def _export_for_ui(self, order):
		result = super(pos_order_line, self)._export_for_ui(order)
		result['line_topping_ids'] = order.line_topping_ids.ids
		return result