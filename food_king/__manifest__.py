# -*- coding: utf-8 -*-
{
    'name': "Food king",
    'summary': "Short summary of the module's purpose",
    'description': """
Long description of the module's purpose
    """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'product', 'om_account_asset', 'pos_restaurant', 'point_of_sale','bi_pos_product_toppings'],
    'data': [
        'views/sync_all_views.xml',
        'views/templates.xml',
        'views/product_view.xml',
        'views/pos_order_view.xml',
        'views/res_company_view.xml',
        'views/food_king_branch_view.xml',
        'data/data.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
  'assets': {
        'point_of_sale.assets': [
            'food_king/static/src/js/custom_js.js',
            'food_king/static/src/xml/pos.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
