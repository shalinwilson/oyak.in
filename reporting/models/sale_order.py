from odoo import models, fields, api
from collections import defaultdict
from datetime import datetime, timedelta

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_mobile = fields.Char(related="partner_id.phone",store=True)
    
#     automation for confirmation
    def action_check_call_detail(self):
        for order in self:
            # Skip if no mobile number
            if not order.partner_mobile:
                continue

            # Search for other sale orders with same mobile that are already confirmed
            existing_order = self.search([
                ('id', '!=', order.id),
                ('partner_mobile', '=', order.partner_mobile),
                ('state', '=', 'sale'),
                ('call_detail', '=', 'confirm'),
            ], limit=1)

            # If such order exists, update call_detail
            if existing_order:
                order.call_detail = 'auto'

    @api.model
    def cron_delete_old_attachments(self, batch_size=250):
        """
        Cron job to delete attachments linked to Sale Orders older than 1 month.
        Deletes in batches of 100 for safety.
        """
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=30)

        # Search attachments linked to sale.order older than one month
        attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('create_date', '<', cutoff_date.strftime('%Y-%m-%d %H:%M:%S'))
        ], limit=batch_size)

        if attachments:
            # log count for monitoring
            _logger = self.env['ir.logging']
            self.env.cr.execute("""
                    INSERT INTO ir_logging(create_date, name, level, message, path, func, line, type, dbuuid)
                    VALUES (NOW(), 'Attachment Cleanup', 'INFO', %s, 'sale_order_attachment_cleanup', 'cron_delete_old_attachments', 0, 'server', %s)
                """, (f"Deleting {len(attachments)} old attachments", self.env.cr.dbname))

            # Delete attachments
            attachments.unlink()

        return True

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