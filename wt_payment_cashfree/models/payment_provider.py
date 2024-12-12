from odoo import api, fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('cashfree', 'Cashfree')], ondelete={'cashfree': 'set default'})
    cashfree_app_id = fields.Char(string='App id', required_if_provider='cashfree', groups='base.group_user')
    cashfree_secret_key = fields.Char(string='Secret Key', required_if_provider='cashfree', groups='base.group_user')

    @api.model
    def _get_cashfree_urls(self, environment):
        if environment == 'prod':
            return 'https://api.cashfree.com/pg'
        else:
            return 'https://sandbox.cashfree.com/pg'

    @api.model
    def _get_cashfree_redirect_urls(self, environment):
        if environment == 'prod':
            return 'https://www.cashfree.com/checkout/post/submit'
        else:
            return 'https://test.cashfree.com/billpay/checkout/post/submit'