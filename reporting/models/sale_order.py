from odoo import models, fields, api
from collections import defaultdict

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def get_consolidated_packing_data(self):
        """
        Aggregate product data across selected sale orders for the packing slip report.
        """
        product_data = defaultdict(lambda: {'name': '', 'size': '', 'quantity': 0})

        for order in self:
            for line in order.order_line:
                if line.product_id.detailed_type == 'product':
                    product_key = (line.product_id.id, line.product_id.size)
                    if not product_data[product_key]['name']:
                        product_data[product_key]['name'] = line.product_id.display_name
                        product_data[product_key]['size'] = line.product_id.size or 'N/A'
                    product_data[product_key]['quantity'] += line.product_uom_qty
        print(product_data.values())
        return list(product_data.values())

    def _get_report_values(self, docids, data=None):
        docs = self.browse(docids)
        consolidated_data = docs.get_consolidated_packing_data()
        return {
            'doc_ids': docids,
            'doc_model': self._name,
            'docs': docs,
            'consolidated_data': consolidated_data,
        }


class SaleOrderReport(models.AbstractModel):
    _name = 'report.reporting.report_sale_slips'
    _description = 'Consolidated Packing Slip Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        sale_orders = self.env['sale.order'].browse(docids)
        product_data = defaultdict(lambda: {'name': '', 'quantity': 0})

        for order in sale_orders:
            for line in order.order_line:
                product_key = (line.product_id.id)
                if not product_data[product_key]['name']:
                    product_data[product_key]['name'] = line.product_id.display_name

                product_data[product_key]['quantity'] += line.product_uom_qty
        print(list(product_data.values()))
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': sale_orders,
            'consolidated_data': list(product_data.values()),
        }