# -*- coding: utf-8 -*-
# Copyright 2018, 2020 Heliconia Solutions Pvt Ltd (https://heliconia.io)

import hashlib
import hmac
import base64

from werkzeug import urls

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_provider import ValidationError
from odoo.tools.float_utils import float_compare
from odoo.tools import consteq, float_round

import logging
import requests
import json

_logger = logging.getLogger(__name__)


class PaymentTransactionCashfree(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, values):
        _logger.info(str(values))
        _logger.info("aas")
        res = super()._get_specific_rendering_values(values)
        if self.provider_code != 'cashfree':
            return res
        base_url = self.get_base_url()
        cashfree_values = dict(appId=self.provider_id.cashfree_app_id,
                               orderId=values['reference'],
                               orderAmount=values['amount'],
                               orderCurrency=values['currency_id'],
                               customerName=values.get('partner_name'),
                               customerEmail=values.get('partner_email'),
                               customerPhone=values.get('partner_phone'),
                               returnUrl=urls.url_join(base_url, '/payment/cashfree/return'),
                               notifyUrl=urls.url_join(base_url, '/payment/cashfree/notify'),
                               )
        cashfree_values['signature'] = self.provider_id._cashfree_generate_sign('out', cashfree_values)
        values.update(cashfree_values)
        _logger.info(values)
        _logger.info("values )))))))))))))))))))")

        response = self.provider_id.get_cashfree_return_url(values)
        _logger.info(response)
        _logger.info("response")
        cashfree_values.update({
            "paymentSessionId": response.get("payment_session_id"),
            "paymentMode": "production" if self.provider_id.state == 'enabled' else "sandbox",
            "returnUrl": response.get("order_meta", {}).get("return_url", ""),
            "notifyUrl": response.get("order_meta", {}).get("notify_url", ""),
        })
        values.update(cashfree_values)
        return cashfree_values

    @api.model
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'cashfree':
            return tx

        reference = notification_data.get('order_id')
        if reference:
            tx = self.search([('reference', '=', reference)], limit=1)
            tx.provider_code = 'cashfree'


        if not tx:
            raise ValidationError(
                "Cashfree: " + _("No transaction found matching reference %s.", reference)
            )
        invalid_parameters = []
        if tx.reference and notification_data.get('order_id') != tx.reference:
            invalid_parameters.append(
                ('Transaction Id', notification_data.get('order_id'), tx.reference))
        if float_compare(float(notification_data.get('order_amount', 0.0)), tx.amount, 2) != 0:
            invalid_parameters.append(
                ('order_amount', notification_data.get('order_amount'), '%.2f' % tx.amount))

        if invalid_parameters:
            _error_message = '%s: incorrect tx data:\n' % (notification_data)
            for item in invalid_parameters:
                _error_message += '\t%s: received %s instead of %s\n' % (item[0], item[1], item[2])
            raise ValidationError(_(_error_message))
        _logger.info("returning from _get_tx_from_notification_data ")
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'cashfree':
            return
        status = notification_data.get('order_status')
        self.write({
            'provider_reference': notification_data.get('referenceId'),
        })
        _logger.info(self.provider_reference, notification_data)
        _logger.info("returning from _process_notification_data ")

        if status == 'PAID':
            self._set_done()
        elif status in ['FAILED', 'CANCELLED', 'FLAGGED']:
            self._set_canceled()
        else:
            self._set_pending()
