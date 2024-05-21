from odoo import models, fields, api, _

class RazorpayAmounts(models.Model):
    _name = 'razorpay.amount'

    name = fields.Char("sale order")
    so_id = fields.Many2one('sale.order')
    credit = fields.Float('Credited Amount')


    def sync_so(self):
        so = self.env['sale.order'].search([('name','=',self.name)],limit=1)
        if not so:
            so_num = self.name.split('-', 1)
            so_num = so_num[0]
            so = self.env['sale.order'].search([('name','=',so_num)],limit=1)
        if so:
            self.so_id = so.id
            so.cod_collected = self.credit