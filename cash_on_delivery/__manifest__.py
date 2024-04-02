# -*- coding: utf-8 -*-
{
    "name": "Website Cash On Delivery",
    "summary": "",
    "version": "16.0.1.0.0",
    "author": "Jithesh Mp",
    "license": "LGPL-3",
    "application": True,
    "installable": True,
    "depends": [
        'web','sale','website_sale','base','auth_signup','portal','delivery'
    ],
    "data": [
        # "security/ir.model.access.csv",
        "data/data.xml",
        "views/payment_method.xml",
        "views/views.xml",

    ],
    "assets": {
        "web.assets_frontend": [
            # 'website_sale_extend/static/src/css/style.css',
            'cash_on_delivery/static/src/js/payment.js',

        ],
    },
}
