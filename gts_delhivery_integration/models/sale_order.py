from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    slip_generation_date = fields.Date()

    payment_type = fields.Selection([
        ('cod', "COD"),
        ('Pre_paid', 'Pre-Paid'),
    ], string='Payment-Type', compute='_compute_payment_type', store=1)
    state = fields.Selection(selection_add=[('rto', 'RTO order')])
    is_rto_order = fields.Boolean("RTO")
    cod_collected = fields.Float('Amount Collected', tracking=True)
    amount_refunded = fields.Float(tracking=True)

    def get_delivery_cost(self):
        for rec in self:
            cost = 0.0
            for picking in rec.picking_ids:
                cost += picking.delhivery_expense
            rec.delhivery_cost = cost

    delhivery_cost = fields.Float(compute="get_delivery_cost")

    @api.depends('payment_type', 'tracking_number')
    def _get_danger(self):
        for rec in self:
            if rec.payment_type == 'Pre_paid' and (rec.tracking_number == '' or rec.is_rto_order == True):
                rec.danger = True
            else:
                rec.danger = False

    danger = fields.Boolean("prepaid not sent", compute='_get_danger')
    partner_mobile = fields.Char(related="partner_id.phone", store=True)

    @api.depends('picking_ids')
    def _get_tracking_number(self):
        for rec in self:
            tracking = ''
            for picking in rec.picking_ids:
                if picking.state != 'cancel' and picking.waybill:
                    tracking = picking.waybill
                    break
            rec.tracking_number = tracking

    def make_delhivery_order(self):
        if len(self.picking_ids) == 1:
            # all_child = self.env["res.partner"].with_context(active_test=False).search([('id', 'child_of', self.partner_id.ids)])


            try:
                self.picking_ids.create_delhivery_order()
                if self.call_detail != 'waauto':
                    self.call_detail = 'auto'
            except:
                pass

    def return_delivery(self):
        print("wprkig")
        pickings = self.picking_ids.filtered(lambda x: x.waybill != False)
        if len(pickings) == 1:
            action = self.env.ref('stock.act_stock_return_picking').read()[0]
            print('return', action)
            return {
                'type': 'ir.actions.act_window',
                'res_model': action['res_model'],
                'view_mode': action['view_mode'],
                'views': [(False, action['view_id'])],
                'target': 'new',
                'context': {},  # You can add context if needed
                'res_id': pickings.id,
            }

    def rto_order(self):

        self.is_rto_order = True
        #     todo sent msg
        values = {
            'body': 'Your order has CAME BACK as delivery partner couldnt deliver it. Please connect us for any query on +91 9995322259',
            'model': 'sale.order',
            'message_type': 'email',
            'res_id': self.id,
        }
        self.env['mail.message'].sudo().create(values)

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        if 'call_detail' in vals and vals['call_detail'] == 'not_connected':
            for order in self:
                values = {
                    'body': 'We could not reach you on your phone for order confirmation. '
                            'Please connect us for order confirmation on +91 9995322259',
                    'model': 'sale.order',
                    'message_type': 'email',
                    'res_id': order.id,
                }
                self.env['mail.message'].sudo().create(values)
                if order.partner_id.email:  # Ensure customer has an email
                    mail_values = {
                        'subject': 'Order Confirmation - Could not reach you',
                        'body_html': """
                                            <p>Hello {name},</p>
                                            <p>We could not reach you on your phone for order confirmation.</p>
                                            <p>Please connect with us for order confirmation on <b>+91 9995322259</b>.</p>
                                            <p>Regards,<br/>Oyak Team</p>
                                        """.format(name=order.partner_id.name or "Customer"),
                        'email_to': order.partner_id.email,
                        'auto_delete': True,
                    }
                    self.env['mail.mail'].sudo().create(mail_values).send()
        elif 'call_detail' in vals and (vals['call_detail'] in ['confirm', 'auto']):
            if self.payment_type == 'Pre_paid':
                payment = self.env['payment.transaction'].search(
                    [('sale_order_ids', 'in', self.ids), ('state', '=', 'done')])
                if not payment and self.cod_collected < 1:
                    raise UserError(_('Check if they have made the payment'+str(self)))

        return res

    state_id = fields.Many2one('res.country.state', string='State', related='partner_id.state_id')
    city = fields.Char('City', related='partner_id.city')
    zip = fields.Char('ZIP', related='partner_id.zip')
    tracking_number = fields.Char(compute="_get_tracking_number")
    user_cancelled = fields.Boolean()
    is_user_returned = fields.Boolean()
    call_detail = fields.Selection(
        string='Call Detail',
        selection=[('confirm', 'Confirmed'),
                   ('not_connected', 'Not Connected'),
                   ('cancel', 'Cancel'),
                   ('auto', 'Auto Confirm'),
                   ('waauto', 'WA Auto Confirm'),
                   ],
        required=False, tracking=True)

    def action_call_detail(self):
        values = {
            'body': '2nd time we could not reach you on your phone for order confirmation. '
                    'Please connect us for order confirmation on +91 9995322259 or the order will be automatically '
                    'cancelled',
            'model': 'sale.order',
            'message_type': 'email',
            'res_id': self.id,
        }
        self.env['mail.message'].sudo().create(values)
        if self.partner_id.email:  # Ensure customer has an email
            mail_values = {
                'subject': 'Order Confirmation - Could not reach you',
                'body_html': """
                                                    <p>Hello {name},</p>
                                                    <p>We could not reach you on your phone for order confirmation.</p>
                                                    <p>Please connect with us for order confirmation on <b>+91 9995322259</b>.</p>
                                                    <p>Regards,<br/>Oyak Team</p>
                                                """.format(name=self.partner_id.name or "Customer"),
                'email_to': self.partner_id.email,
                'auto_delete': True,
            }
            self.env['mail.mail'].sudo().create(mail_values).send()

    @api.depends('order_line', 'order_line.product_id')
    def _compute_payment_type(self):
        for order in self:
            cod = False
            for line in order.order_line:
                product_name = line.product_id.name
                if 'cod' in product_name or 'Cod' in product_name or 'COD' in product_name or 'cod charges' in product_name or 'Cod Charges' in product_name or 'COD Charges' in product_name:
                    # if line.product_id.name == 'cod' or 'Cod' or 'COD':
                    cod = True
            if cod:
                order.payment_type = 'cod'
            else:
                order.payment_type = 'Pre_paid'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        values.update({
            'payment_type': self.order_id.payment_type or '',
        })
        return values


class SaleReport(models.Model):
    _inherit = "sale.report"

    state_id = fields.Many2one('res.country.state', 'State')
    city = fields.Char('City')
    zip = fields.Char('ZIP')

    # def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
    #     fields['state_id'] = ", partner.state_id"
    #     fields['city'] = ", partner.city"
    #     fields['zip'] = ", partner.zip"
    #     groupby += ', partner.state_id,partner.city,partner.zip'
    #     return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
