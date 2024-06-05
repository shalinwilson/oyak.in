# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Shijin V (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

from odoo.addons.website.controllers import main
from datetime import datetime
from odoo import http
from odoo.exceptions import UserError
from odoo.http import request


class SaleOrderController(http.Controller):
    @http.route('/cancel_order', type='json', auth='public',website=True)
    def cancel_order(self, **kwargs):
        try:
            # Fetch the sale order by its ID
            order_id = kwargs.get('order_id')
            order = request.env['sale.order'].sudo().browse(order_id)
            print(order)
            # Check if the order has a tracking number
            if order.tracking_number:
                # If the order has a tracking number, raise a UserError
                return {'success': False, 'error': ' Item Already shipped'}
            print(order)
            print("working")
            # Cancel the sale order
            order.with_context({'disable_cancel_warning': True}).action_cancel()
            order.user_cancelled = True
            print(order.state)

            # Return success response
            return {'success': True, 'message': 'Order canceled successfully'}
        except UserError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': 'An error occurred while canceling the order'}


class CustomerRegistration(main.Home):

    @http.route('/sale_return', type='http', methods=['POST'], auth="public", website=True,
                csrf=False)
    def sale_return(self, **kwargs):
        """Controller to create return order"""
        product_id = request.env['product.product'].sudo().search([('id', '=', int(kwargs['product']))])
        order = request.env['sale.order'].sudo().search([('id', '=', int(kwargs['order_id']))])
        qty = kwargs['qty']
        reason = kwargs['reason']
        values = {
            'partner_id': order.partner_id.id,
            'sale_order': order.id,
            'product_id': product_id.id,
            'quantity': qty,
            'reason': reason,
            'user_id': request.env.uid,
            'create_date': datetime.now(),
        }
        # stock_picks = request.env['stock.picking'].search([('origin', '=', order.name)])
        # moves = stock_picks.mapped('move_ids_without_package').with_user(1).filtered(
        #     lambda p: p.product_id == product_id)
        # if moves:
        #     moves = moves.sorted('product_uom_qty', reverse=True)
        values.update({'state': 'draft'})
        ret_order = request.env['sale.return'].with_user(1).create(values)
        order.is_user_returned = True
            # moves[0].picking_id.return_order = ret_order.id
            # moves[0].picking_id.return_order_picking = False
        return request.redirect('/my/request-thank-you')

    @http.route('/my/request-thank-you', website=True, page=True, auth='public', csrf=False)
    def maintenance_request_thanks(self):
        return request.render('website_return_management.customers_request_thank_page')
