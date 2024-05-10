from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_type = fields.Selection([
        ('cod', "COD"),
        ('Pre_paid', 'Pre-Paid'),
    ], string='Payment-Type', compute='_compute_payment_type')

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
            all_child = self.env["res.partner"].with_context(active_test=False).search([('id', 'child_of', self.partner_id.ids)])
            so = self.env["sale.order"].search([("partner_id", "in", all_child.ids)])
            so_count = len(so.filtered(lambda x:x.state=='sale'))
            if so_count < 2:
                try:
                    if self.picking_ids:
                        self.picking_ids.create_delhivery_order()
                except:
                    pass



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