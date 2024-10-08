{
    'name': 'ODOO Delhivery Integration',
    'author': 'Geotechnosoft',
    'website': 'http://www.geotechnosoft.com',
    'summary': 'You can Book your shipment directly from the order',
    'description': """shipment, shipment integration,Delhivery Integration ,delhivery, integration , shipment integration, odoo shipment,shipment odoo,
     integration,""",
    'depends': ['base', 'stock', 'mail', 'sale', 'delivery', 'website_sale',
                "account",'website_sale_stock',],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/order_picking.xml',
        'views/configuration_view.xml',
        'views/stock_picking_inherit.xml',
        'views/stock_warehouse_inherit.xml',
        'views/sale_order_inherit.xml',
        'views/website_order_template.xml',
        'reports/reports.xml',
        'reports/waybill_slip.xml',
        'views/stock_move.xml',
        'views/cod_details.xml',
        'views/delhivery_expenses.xml',
        'views/razorpay_amount.xml',
        'data/pincode_crone.xml',
    ],
    'images': ['static/description/banner.png','static/src/img/delhiverylogo.png'],
    'price': 20,
    'currency': 'USD',
    'license': 'OPL-1',
    'application': True,
    'installable': True,

}
