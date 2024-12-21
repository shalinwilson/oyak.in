# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Payment Cashfree',
    'version': '17.0',
    'category': 'Accounting/Payment Providers',
    'summary': '',
    'author': 'Warlock Technologies Pvt Ltd.',
    'website': 'http://warlocktechnologies.com',
    'support': 'mailto:support@warlocktechnologies.com',
    'depends': ['account_payment','payment'],
    'data': [
        # "views/payment_cashfree_templates.xml",
        # "views/payment_provider_form.xml",
        # "data/payment_provider_data.xml",
        # "views/payment_templates.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            '/wt_payment_cashfree/static/src/js/payment_form.js',
        ]
    },
    'images': ['images/screen_image.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'OPL-1',
}

