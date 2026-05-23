# -*- coding: utf-8 -*-
{
    'name': "Coin System",

    'summary': """
        website coin system for a refered prepaid sale order """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Oyak.in",
    'website': "https://www.oyak.in",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/packing_list.xml',
        # 'views/templates.xml',
    ],

}
