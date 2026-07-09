from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.website_sale_delivery.controllers.main import WebsiteSaleDelivery

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
# todo controller for passing data of payment methods with carrier update for charges in default Odoo code

    class WebsiteSaleDeliveryInherit(WebsiteSaleDelivery):

        @http.route(
            ['/shop/update_carrier'],
            type='json',
            auth='public',
            methods=['POST'],
            website=True,
            csrf=False,
        )
        def update_eshop_carrier(self, **post):
            # Execute Odoo's original logic
            result = super().update_eshop_carrier(**post)

            order = request.website.sale_get_order()

            if not order:
                return result

            carrier = order.carrier_id
            allowed = request.env['payment.provider'].sudo().search([
                ('state', '=', 'test'),
            ])

            if carrier.is_cash_on_delivery:
                allowed = allowed.filtered(lambda p: p.is_cash_on_delivery)
            else:
                allowed = allowed.filtered(lambda p: not p.is_cash_on_delivery)
            print(allowed)
            result.update({
                'allowed_provider_ids': allowed.ids,
            })
            return result