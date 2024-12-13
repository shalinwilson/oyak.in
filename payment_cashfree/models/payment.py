# -*- coding: utf-8 -*-
# Copyright 2018, 2020 Heliconia Solutions Pvt Ltd (https://heliconia.io)

import hashlib
import hmac
import base64

from werkzeug import urls

from odoo import api, fields, models, _

import logging
import requests
import json

_logger = logging.getLogger(__name__)


class PaymentAcquirerCashfree(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('cashfree', 'Cashfree')], ondelete={'cashfree': 'set default'})
    cashfree_app_id = fields.Char(string='App id', required_if_provider='cashfree', groups='base.group_user')
    cashfree_secret_key = fields.Char(string='Secret Key', required_if_provider='cashfree', groups='base.group_user')
    cashfree_version = fields.Char(string="API Version")

    def get_api_header(self):
        return {
              'x-client-id': self.cashfree_app_id,
              'x-client-secret': self.cashfree_secret_key,
              'x-api-version': self.cashfree_version,
              'Content-Type': 'application/json'
            }

    def _get_cashfree_urls(self, environment):
        """ Cashfree URLs"""
        if environment == 'prod':
            return {'cashfree_form_url': 'https://api.cashfree.com/pg'}
        else:
            return {'cashfree_form_url': 'https://sandbox.cashfree.com/pg'}

    def _cashfree_get_customer(self, mobile, email, name):
        url = self.cashfree_get_form_action_url() + "/customers"
        payload = json.dumps({
            "customer_phone": mobile,
            "customer_email": email,
            "customer_name": name
        })
        headers = self.get_api_header()
        response = requests.request("POST", url, headers=headers, data=payload)
        result = json.loads(response.text)
        result['customer_uid'] = result.pop("customer_uid", "")
        result['customer_email'] = email
        result['customer_name'] = name
        return result

    def _cashfree_generate_sign(self, inout, postData):
        if inout not in ('in', 'out'):
            raise Exception("Type must be 'in' or 'out'")
        message = False
        if inout == 'out':
            sortedKeys = sorted(postData)
            signatureData = ""
            for key in sortedKeys:
                signatureData += key + str(postData[key]);
            message = signatureData.encode('utf-8')

        elif inout == 'in':
            signatureData = postData["orderId"] + postData["orderAmount"] + postData["referenceId"] + \
                            postData["txStatus"] + postData["paymentMode"] + postData["txMsg"] + postData["txTime"]
            message = signatureData.encode('utf-8')
        secret = self.cashfree_secret_key.encode('utf-8')
        signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
        return signature


    def cashfree_get_form_action_url(self):
        self.ensure_one()
        environment = "prod" if self.state == 'enabled' else "sandbox"
        return self._get_cashfree_urls(environment)['cashfree_form_url']

    def get_cashfree_return_url(self, values):
        self.ensure_one()
        url = self.cashfree_get_form_action_url() + "/orders"
        order_name = values.get('reference').split('-')[0]
        order_id = self.env['sale.order'].sudo().search([('name', '=', order_name)], limit=1)
        customer_details = {
            "customer_id": 'CU' + str(order_id.partner_id.id),
            "customer_name": order_id.partner_id.name,
            "customer_email": order_id.partner_id.email,
            "customer_phone": order_id.partner_id.phone.replace(" ", ""),
        }
        data = {
            "customer_details": customer_details,
            "order_meta": {
                "return_url": values.get("returnUrl") + "?order_id=" + values.get("orderId"),
                "notify_url": values.get("notifyUrl") + "?order_id=" + values.get("orderId"),
            },
            "order_amount": values.get("amount"),
            "order_currency": "INR",
            "order_id": values.get("reference")
        }
        payload = json.dumps(data)
        headers = self.get_api_header()
        response = requests.request("POST", url, headers=headers, data=payload)
        print(response,"asd")
        return json.loads(response.text)
