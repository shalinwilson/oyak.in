from odoo import models, fields, api
from collections import defaultdict

class SaleOrder(models.Model):
    _inherit = 'sale.order'



class SaleOrderReport(models.AbstractModel):
    _name = 'report.reporting.report_sale_slips'
    _description = 'Consolidated Packing Slip Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        sale_orders = self.env['sale.order'].browse(docids)
        product_data = defaultdict(lambda: {'name': '', 'quantity': 0})

        for order in sale_orders:
            for line in order.order_line:
                if line.product_id.detailed_type == 'product':
                    product_key = (line.product_id.id)
                    if not product_data[product_key]['name']:
                        product_data[product_key]['name'] = line.product_id.display_name

                    product_data[product_key]['quantity'] += line.product_uom_qty
        print(list(product_data.values()))
        consolidated_data = sorted(product_data.values(), key=lambda x: x['name'])
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': sale_orders,
            'consolidated_data': consolidated_data
        }