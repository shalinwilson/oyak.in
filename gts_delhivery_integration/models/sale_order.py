from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_type = fields.Selection([
        ('cod', "COD"),
        ('Pre_paid', 'Pre-Paid'),
    ], string='Payment-Type', compute='_compute_payment_type', store=1)
    state = fields.Selection(selection_add=[('rto', 'RTO order')])
    is_rto_order = fields.Boolean("RTO")
    cod_collected = fields.Float('Amount Collected', tracking=True)
    amount_refunded = fields.Float(tracking=True)

    @api.depends('payment_type','tracking_number')
    def _get_danger(self):
        for rec in self:
            if rec.payment_type == 'Pre_paid' and (rec.tracking_number == '' or rec.is_rto_order == True):
                rec.danger = True
            else:
                rec.danger = False


    danger = fields.Float("prepaid not sent",compute='_get_danger')
    @api.depends('partner_id')
    def get_mobile_num(self):
        for rec in self:
            rec.partner_mobile = rec.partner_id.phone or rec.partner_id.mobile

    partner_mobile = fields.Char(compute="get_mobile_num")

    @api.depends('picking_ids')
    def _get_tracking_number(self):
        for rec in self:
            for picking in rec.picking_ids:
                if picking.state != 'cancel':
                    if picking.waybill:
                        rec.tracking_number = picking.waybill
                    else:
                        rec.tracking_number = ''
                else:
                    rec.tracking_number = ''
            if not rec.picking_ids:
                rec.tracking_number = ''

    def make_delhivery_order(self):
        if len(self.picking_ids) == 1:
            # all_child = self.env["res.partner"].with_context(active_test=False).search([('id', 'child_of', self.partner_id.ids)])
            so = self.env["sale.order"].search(
                [("partner_id", "in", self.partner_id.ids), ('tracking_number', '!=', False)])

            so_count = len(so.filtered(lambda x: x.state == 'sale'))
            if so_count <= 2:
                try:
                    self.picking_ids.create_delhivery_order()
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

    @api.onchange('call_detail')
    def onchange_call_detail(self):
        if self.call_detail == 'not_connected':
            values = {
                'body': 'we could not reach you on your phone for order confirmation '
                        'Please connect us for order confirmation on +91 9995322259',
                'model': 'sale.order',
                'message_type': 'email',
                'res_id': self.id,
            }
            self.env['mail.message'].sudo().create(values)

    state_id = fields.Many2one('res.country.state', string='State', related='partner_id.state_id')
    city = fields.Char('City', related='partner_id.city')
    zip = fields.Char('ZIP', related='partner_id.zip')
    tracking_number = fields.Char(compute="_get_tracking_number")
    call_detail = fields.Selection(
        string='Call Detail',
        selection=[('confirm', 'Confirmed'),
                   ('not_connected', 'Not Connected'),
                   ('cancel', 'Cancel'),
                   ],
        required=False, tracking=True)

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
