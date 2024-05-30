from odoo import models, fields, api, _
from odoo.exceptions import UserError
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



class DelhiveryExp(models.Model):
    _name = 'delhivery.exp'



    exp_amount = fields.Float('Miles or amount')
    tracking_number = fields.Char('AWB')

    def sync_so(self):
        picking = self.env['stock.picking'].search([('waybill','=',self.tracking_number)],limit=1)
        if not picking:
            raise UserError(_("couldnt find picking for %s",self.tracking_number))
        else:
            picking.delhivery_expense += self.exp_amount
