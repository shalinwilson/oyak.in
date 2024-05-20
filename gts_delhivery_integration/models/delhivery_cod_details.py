from odoo import models, fields, api, _

class DelhiveryCod(models.Model):
    _name = 'delhivery.cod'

    name = fields.Char("sale order")
    so_id = fields.Many2one('sale.order')
    cod_amount = fields.Float('Cod Amount')
    tracking_number = fields.Char('Tracking Number')

    def sync_so(self):
        so = self.env['sale.order'].search([('name','=',self.name)],limit=1)
        if not so:
            so = self.env['sale.order'].search([('tracking_number','=',self.tracking_number)],limit=1)
        if so:
            self.so_id = so.id
            so.cod_collected = self.cod_amount