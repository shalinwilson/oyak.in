# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'


    is_cash_on_delivery = fields.Boolean(default=False)


    @api.model
    def get_delivery_charge_product(self, order_id):
        order_lines = self.env['sale.order.line'].search([('order_id', '=', order_id)])
        for line in order_lines:
            if line.product_id.default_code == 'Delivery_1000':  # Assuming delivery charges are represented as service type products
                return line.product_id
        return False
