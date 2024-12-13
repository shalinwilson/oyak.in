# -*- coding: utf-8 -*-
# Copyright 2018, 2020 Heliconia Solutions Pvt Ltd (https://heliconia.io)

import logging
import pprint
import werkzeug
import requests
import json

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CashfreeController(http.Controller):

    @http.route(['/payment/cashfree/return', '/payment/cashfree/cancel', '/payment/cashfree/error',
                 '/payment/cashfree/notify'], type='http', auth='public', csrf=False)
    def cashfree_return(self, **post):
        """ Cashfree."""
        acquirer_id = request.env.ref('payment_cashfree.payment_acquirer_cashfree').sudo()
        if acquirer_id and post.get('order_id'):
            header = acquirer_id.get_api_header()
            url = acquirer_id.cashfree_get_form_action_url()
            order_url = url + '/orders/' + post.get('order_id')
            response = requests.post(order_url, headers=header)
            if response.status_code == 200:
                response_val = json.loads(response.text)
                _logger.info(
                    'Cashfree: entering form_feedback with post data %s', pprint.pformat(response_val))
                if post:
                    tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                        'cashfree',post
                    )

                    tx_sudo._process_notification_data('cashfree', response_val)
        return werkzeug.utils.redirect('/payment/status')
