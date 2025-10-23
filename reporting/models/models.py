# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cost_for_reporting = fields.Integer()

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_split = fields.Boolean()
class reporting(models.Model):
    _name = 'reporting.reporting'
    _description = 'reporting.reporting'

    date1 = fields.Datetime()
    date2 = fields.Datetime()
    sales_amount_collected = fields.Float()
    total_amount_refunded = fields.Float()
    shipping_cost_total = fields.Float()
    other_deductions = fields.Float()
    profit_against_collected_amount = fields.Float()
    revenue_pro_percent = fields.Float()

    total_orders = fields.Integer()
    total_cod = fields.Integer()
    total_prepaid = fields.Integer()
    cod_prepaid_ratio = fields.Float("COD %")
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
        so_in_period = self.env['sale.order'].search([('date_order', '>=', start_date),
                                                      ('date_order', '<=', end_date),
                                                      ('state', 'not in', ['draft', 'sent', 'cancel'])
                                                      ])
        so_in_period = so_in_period.filtered(lambda x:x.cod_collected > 0)
        self.total_orders = len(so_in_period.filtered(lambda x: x.is_rto_order == False))
        self.total_cod = len(so_in_period.filtered(lambda self: self.payment_type == 'cod'))
        self.total_prepaid = len(so_in_period.filtered(lambda self: self.payment_type == 'Pre_paid'))
        print(self.total_cod,self.total_orders,"workinggggg")
        self.cod_prepaid_ratio = (self.total_cod / self.total_orders) * 100

        self.total_rto_orders = self.env['sale.order'].search_count([('date_order', '>=', start_date),
                                                                     ('date_order', '<=', end_date),
                                                                     ('is_rto_order', '=', True),
                                                                     ])
        self.rto_loss = sum(self.env['sale.order'].search([('date_order', '>=', start_date),
                                                           ('date_order', '<=', end_date),
                                                           ('is_rto_order', '=', True)
                                                           ]).mapped('delhivery_cost'))
        delhivery_partner = self.env['res.partner'].search([('name', '=', 'Delhivery')], limit=1)
        delhivery_payments = self.env['account.payment'].search([('date', '>=', start_date),
                                                                 ('date', '<=', end_date),
                                                                 ('state', '=', 'posted'),
                                                                 ('partner_id', '=', delhivery_partner.id),
                                                                 ('payment_type', '=', 'outbound')
                                                                 ])
        spliting_bills = self.env['account.move'].search([('date', '>=', start_date),
                                                                 ('date', '<=', end_date),
                                                                 ('state', '=', 'posted'),
                                                          ('is_split','=',True),
                                                                 ('move_type', '=', 'in_invoice')
                                                                 ])

        split_amount = sum(spliting_bills.mapped('amount_total'))
        print(split_amount)
        self.other_deductions = split_amount
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

        self.calculated_profit = self.sales_amount_collected - (self.shipping_cost_total + self.total_amount_refunded
                                                                + self.products_total_cost + self.other_deductions)

        self.profit_against_collected_amount = (self.calculated_profit / (
                    self.sales_amount_collected - self.shipping_cost_total)) * 100
        self.revenue_pro_percent = (self.calculated_profit / self.sales_amount_collected ) * 100



# forcasted quantity report
class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_no_forecast_products(self):
        result = []
        for template in self:
            if not template.attribute_line_ids:
                continue

            # Sort by attribute sequence (not line)
            first_line = template.attribute_line_ids.sorted(key=lambda l: l.attribute_id.sequence)[0]

            attribute = first_line.attribute_id
            first_value = first_line.value_ids.sorted(key=lambda v: v.sequence)[0] if first_line.value_ids else False
            if not first_value:
                continue

            # Find variant that contains this first attribute value
            variant = template.product_variant_ids.filtered(
                lambda v: first_value in v.product_template_attribute_value_ids.mapped('product_attribute_value_id')
            )
            if not variant:
                continue

            first_variant = variant[0]
            forecast = first_variant.virtual_available or 0.0

            if forecast <= 0:
                result.append({
                    'product_name': template.name,
                    'variant_name': first_variant.display_name,
                    'forecast_qty': forecast,
                    'sequence': first_variant.sequence,
                })

        return result

