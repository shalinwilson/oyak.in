from odoo.addons.website_sale.controllers.main import WebsiteSale
from collections import defaultdict
# from itertools import product as cartesian_product
# import json
# import logging
# from datetime import datetime
# from werkzeug.exceptions import Forbidden, NotFound
# from werkzeug.urls import url_decode, url_encode, url_parse

from odoo import fields, http, SUPERUSER_ID, tools, _
# from odoo.fields import Command
from odoo.http import request
# from odoo.addons.base.models.ir_qweb_fields import nl2br
# from odoo.addons.http_routing.models.ir_http import slug
# from odoo.addons.payment import utils as payment_utils
# from odoo.addons.payment.controllers import portal as payment_portal
# from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
# from odoo.addons.website.controllers.main import QueryURL
# from odoo.addons.website.models.ir_http import sitemap_qs2dom
# from odoo.exceptions import AccessError, MissingError, ValidationError
# from odoo.addons.portal.controllers.portal import _build_url_w_params
# from odoo.addons.website.controllers import main
# from odoo.addons.website.controllers.form import WebsiteForm
# from odoo.addons.sale.controllers import portal
# from odoo.osv import expression
# from odoo.tools import lazy
# from odoo.tools.json import scriptsafe as json_scriptsafe

class WebsiteSaleConfirmInherits(WebsiteSale):

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            payment_tx_id = order.get_portal_last_transaction()
            if payment_tx_id.provider_id.is_cash_on_delivery:
                order.action_confirm()
        res = super(WebsiteSaleConfirmInherits, self).shop_payment_confirmation(**post)

        return res
