import base64
import logging
import requests
import json
from uuid import uuid4
from werkzeug import urls
import hashlib
import hmac

from odoo import api, models, fields, _
from odoo.addons.wt_payment_cashfree.controllers.main import CashfreeController
from odoo.addons.payment.models.payment_provider import ValidationError
from odoo.tools.float_utils import float_round, float_compare
# from odoo.addons.payment_stripe.const import STATUS_MAPPING, PAYMENT_METHOD_TYPES

_logger = logging.getLogger(__name__)


INT_CURRENCIES = [
    u'BIF', u'XAF', u'XPF', u'CLP', u'KMF', u'DJF', u'GNF', u'JPY', u'MGA', u'PYG', u'RWF', u'KRW',
    u'VUV', u'VND', u'XOF'
]

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    cashfree_token = fields.Char('Saferpay Token')

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'cashfree':
            return res
        self.ensure_one()
        base_url = self.get_base_url()
        environment = 'prod' if self.provider_id.state == 'enabled' else 'test'
        tx = self.env['payment.transaction'].search([('reference', '=', processing_values['reference'])], limit=1)
        order_name = processing_values.get('reference').split('-')[0]
        order_id = self.env['sale.order'].sudo().search([('name','=',order_name)],limit=1)
        cashfree_url = self.provider_id._get_cashfree_urls(environment) + '/orders'
        header = {
            'x-client-id': self.provider_id.cashfree_app_id,
            'x-client-secret': self.provider_id.cashfree_secret_key,
            'x-api-version': '2022-09-01',
            'Content-Type': 'application/json',
        }
        data = {
            "order_id": processing_values.get('reference'),
            "order_amount": order_id.amount_total,
            "order_currency": order_id.currency_id.name,
            "order_note": None,
            "customer_details": {
                "customer_id": 'CU' + str(order_id.partner_id.id),
                "customer_name": order_id.partner_id.name,
                "customer_email": order_id.partner_id.email,
                "customer_phone": order_id.partner_id.phone,
            },
            "order_meta": {
                "return_url": base_url+'/cashfree/payment/validate?order_id={order_id}',
                # "notifyUrl": base_url+'/cashfree/payment/notify?order_id={order_id}',
            },
        }

        response = requests.post(cashfree_url, headers=header, data=json.dumps(data))
        response_val = response.json()
        if response.status_code != 200:
            raise ValidationError(_("RESP %s %s" % (response.status_code, response_val.get('message'))))

        processing_values.update(response_val)
        processing_values['status'] = self.provider_id.state
        return processing_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'cashfree' or len(tx) == 1:
            return tx

        reference = notification_data.get('order_id')
        if reference:
            tx = self.search([('reference', '=', reference)], limit=1)
            tx.provider_reference = 'cashfree'

        if not tx:
            raise ValidationError(
                "Cashfree: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'cashfree':
            return
        if notification_data.get('order_status') == 'PAID':
            self._set_done()
            self._finalize_post_processing()
        elif notification_data.get('order_status') == "ACTIVE":
            self._set_pending()
        else:
            _logger.warning("saferpay: The transaction with reference %s was cancelled (reason: %s)", notification_data.get('order_id'), notification_data.get('order_status'))
            self._set_canceled()
            msg = 'Received unrecognized response for cashfree Payment %s, set as error' % (notification_data.get('order_id'))
            _logger.info(msg)
            self._set_error(msg)
