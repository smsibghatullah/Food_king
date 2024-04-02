# -*- coding: utf-8 -*-
{
    'name': "Food king",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base', 'product','om_account_asset','pos_restaurant','point_of_sale'],

    'data': [
        'views/sync_all_views.xml',
        'views/templates.xml',
        'views/product_view.xml',
        'views/pos_order_view.xml',
        'data/data.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
    'static/src/xml/*.xml',
     ],
    'web.assets_backend': [
        'food_king/static/src/**/*.js',
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

