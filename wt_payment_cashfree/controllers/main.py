import logging
from odoo import http
from odoo.http import request
import requests
import werkzeug
from werkzeug import urls

_logger = logging.getLogger(__name__)

class CashfreeController(http.Controller):

	_return_url = '/cashfree/payment/validate'
	_notify_url = '/cashfree/payment/notify'

	@http.route('/cashfree/payment/validate', type='http', auth="public", methods=['POST','GET'], csrf=False)
	def cashfree_validate(self, **post):
		provider_id = request.env.ref('wt_payment_cashfree.payment_acquirer_cashfree').sudo()
		if provider_id and post.get('order_id'):
			header = {
				'x-client-id': provider_id.cashfree_app_id,
				'x-client-secret': provider_id.cashfree_secret_key,
				'x-api-version': '2022-09-01',
				'Content-Type': 'application/json',
			}
			environment = 'prod' if provider_id.state == 'enabled' else 'test'
			url = provider_id._get_cashfree_urls(environment)
			order_url = url+'/orders/'+post.get('order_id')
			response = requests.post(order_url, headers=header)
			if response.status_code == 200:
				response_val = response.json()
				order_name = response_val.get('order_id').split('-')[0]
				# if response_val.get('order_status') == 'PAID':
				if request.session.get('sale_order_id'):
					order_id = request.env['sale.order'].sudo().browse(int(request.session.get('sale_order_id')))
				if order_id and (order_id.name != order_name):
					order_id = request.env['sale.order'].sudo().search([('name','=',order_name)])
				
				if order_id:
					tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('cashfree', response_val)
					tx_sudo._handle_notification_data('stripe', response_val)

			# if response.status_code != 200:
            	# raise ValidationError(_("RESP %s %s" % (response.status_code, response_val.get('message'))))
			
		return request.redirect('/shop/confirmation')

	@http.route(_notify_url, type='http', auth="public", methods=['POST'], csrf=False)
	def cashfree_notify(self, **post):
		# import pdb;pdb.set_trace()
		return request.redirect('/shop/confirmation')