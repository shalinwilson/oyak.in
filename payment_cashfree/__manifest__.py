# -*- coding: utf-8 -*-
# Copyright 2018, 2020 Heliconia Solutions Pvt Ltd (https://heliconia.io)

{
    'name': "Payment Cashfree",
    'summary': """Payment Acquirer: Cashfree Implementation""",
    'description': """Payment Acquirer: Cashfree Implementation""",
    'category': 'Payment Acquirer',

    'author': 'Heliconia Solutions Pvt. Ltd.',
    'company': 'Heliconia Solutions Pvt. Ltd.',
    'website': 'https://heliconia.io',

    'version': '15.0.1.0.0',
    'license': 'OPL-1',
    'depends': ['payment', 'web','sale'],
    'data': [
        'views/payment_views.xml',
        'views/payment_cashfree_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_cashfree/static/src/js/cashfree.js',
        ],
    },

    'images': ['static/description/heliconia_odoo_cashfree.gif'],

    'uninstall_hook': 'uninstall_hook',

}
