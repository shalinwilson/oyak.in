# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cost_for_reporting = fields.Integer()

class reporting(models.Model):
    _name = 'reporting.reporting'
    _description = 'reporting.reporting'

    name = fields.Char()
    date1 = fields.Datetime()
    date2 = fields.Datetime()
    sales_amount_collected = fields.Float()
    total_amount_refunded = fields.Float()
    shipping_cost_total = fields.Float()
    other_deductions = fields.Float()

    total_orders = fields.Integer()
    total_cod = fields.Integer()
    total_prepaid = fields.Integer()
    cod_prepaid_ratio = fields.Float()
    total_rto_orders = fields.Float()
    rto_loss = fields.Float()
    delivery_payments_total = fields.Float()
    products_total_cost = fields.Float()

    calculated_profit = fields.Float()
    note = fields.Char()
    def calculate_values(self):
        print("working")
        start_date = fields.Datetime.to_string(self.date1)
        end_date = fields.Datetime.to_string(self.date2)
        print(self.env['sale.order'].browse([1]).date_order)
        so_in_period = self.env['sale.order'].search([('date_order','>=',start_date),
                                                      ('date_order','<=',end_date),
                                                      ('state','not in',['draft','sent','cancel'])
                                                      ])
        self.total_orders = len(so_in_period.filtered(lambda x: x.is_rto_order == False))
        self.total_cod = len(so_in_period.filtered(lambda self: self.payment_type == 'cod'))
        self.total_prepaid = len(so_in_period.filtered(lambda self: self.payment_type == 'Pre_paid'))
        self.cod_prepaid_ratio = (self.total_prepaid / self.total_cod)
        self.total_rto_orders = self.env['sale.order'].search_count([('date_order','>=',start_date),
                                                      ('date_order','<=',end_date),
                                                          ('is_rto_order','=',True),
                                                      ])
        self.rto_loss = sum(self.env['sale.order'].search([('date_order','>=',start_date),
                                                      ('date_order','<=',end_date),
                                                          ('is_rto_order','=',True)
                                                      ]).mapped('delhivery_cost'))
        delhivery_partner  = self.env['res.partner'].search([('name','=','Delhivery')],limit=1)
        delhivery_payments = self.env['account.payment'].search([('date','>=',start_date),
                                                      ('date','<=',end_date),
                                                              ('state','=','posted'),
                                                              ('partner_id','=',delhivery_partner.id),
                                                              ('payment_type','=','outbound')
                                                              ])
        self.note = str(delhivery_payments) + str(delhivery_partner)
        self.delivery_payments_total = sum(delhivery_payments.mapped('amount_total'))



        self.sales_amount_collected = sum(so_in_period.mapped('cod_collected'))
        self.shipping_cost_total = sum(so_in_period.mapped('delhivery_cost'))
        self.total_amount_refunded = sum(so_in_period.mapped('amount_refunded'))

        products_cost = 0
        for so in so_in_period:
            if not so.is_rto_order:
                for sol in so.order_line:
                    products_cost += (sol.product_id.cost_for_reporting * sol.product_uom_qty)

        self.products_total_cost = products_cost

        self.calculated_profit = self.sales_amount_collected - (self.shipping_cost_total+self.total_amount_refunded
                                                                +self.products_total_cost+self.other_deductions)











