from odoo import models, fields, api
from collections import defaultdict
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


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
            attachments.unlink()
            _logger.info(f"deleted ============: {attachments}")
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

class OyakInventoryReportWizard(models.TransientModel):
    _name = 'oyak.inventory.report.wizard'
    _description = 'Oyak Inventory Report Wizard'

    weekly_top_products = fields.Boolean(
        string="Weekly Top 20 Products"
    )

    fast_moving_products = fields.Boolean(
        string="Fast Moving Products"
    )
    top_category = fields.Boolean(
        string="Category Summery"
    )

    restock_priority = fields.Boolean(
        string="Restock Priority"
    )

    dead_stock = fields.Boolean(
        string="Dead Stock"
    )

    # common date range
    date_from = fields.Date(
        string="From Date"
    )

    date_to = fields.Date(
        string="To Date"
    )

    lookback_days = fields.Integer(
        string="Lookback Days",
        default=30
    )

    minimum_stock_days = fields.Integer(
        string="Minimum Stock Days",
        default=15
    )

    dead_stock_days = fields.Integer(
        string="No Sales Since (Days)",
        default=60
    )

    def _get_top_products(self):
        domain = [
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', self.date_from),
            ('order_id.date_order', '<=', self.date_to),
            ('product_id.detailed_type', '=', 'product'),
        ]

        # -----------------------------
        # Top Products by Quantity
        # -----------------------------
        qty_result = self.env['sale.order.line'].read_group(
            domain=domain,
            fields=[
                'product_id',
                'product_uom_qty:sum',
            ],
            groupby=[
                'product_id',
            ],
            lazy=False,
        )

        qty_products = {}

        for row in qty_result:
            product = self.env['product.product'].browse(row['product_id'][0])
            tmpl = product.product_tmpl_id

            if tmpl.id not in qty_products:
                qty_products[tmpl.id] = {
                    'product_tmpl_id': tmpl.id,
                    'product_name': tmpl.name,
                    'qty_sold': 0,
                    'orders': 0,
                }

            qty_products[tmpl.id]['qty_sold'] += row['product_uom_qty']
            qty_products[tmpl.id]['orders'] += row.get('__count', 0)

        qty_data = sorted(
            qty_products.values(),
            key=lambda x: x['qty_sold'],
            reverse=True
        )[:20]

        # -----------------------------
        # Top Products by Revenue
        # -----------------------------
        revenue_result = self.env['sale.order.line'].read_group(
            domain=domain,
            fields=[
                'product_id',
                'price_subtotal:sum',
            ],
            groupby=[
                'product_id',
            ],
            lazy=False,
        )

        revenue_products = {}

        for row in revenue_result:
            product = self.env['product.product'].browse(row['product_id'][0])
            tmpl = product.product_tmpl_id

            if tmpl.id not in revenue_products:
                revenue_products[tmpl.id] = {
                    'product_tmpl_id': tmpl.id,
                    'product_name': tmpl.name,
                    'revenue': 0.0,
                    'orders': 0,
                }

            revenue_products[tmpl.id]['revenue'] += row['price_subtotal']
            revenue_products[tmpl.id]['orders'] += row.get('__count', 0)

        revenue_data = sorted(
            revenue_products.values(),
            key=lambda x: x['revenue'],
            reverse=True
        )[:20]

        return {
            'by_qty': qty_data,
            'by_revenue': revenue_data,
        }
    # def _get_fast_moving_products(self):
    #     days = (
    #                    self.date_to - self.date_from
    #            ).days + 1
    #
    #     sales = self.env['sale.order.line'].read_group(
    #         domain=[
    #             ('order_id.state', 'in', ['sale', 'done']),
    #             ('order_id.date_order', '>=', self.date_from),
    #             ('order_id.date_order', '<=', self.date_to),
    #         ],
    #         fields=[
    #             'product_id',
    #             'product_uom_qty:sum',
    #         ],
    #         groupby=['product_id'],
    #     )
    #
    #     results = []
    #
    #     for row in sales:
    #         product_id = row['product_id'][0]
    #
    #         product = self.env['product.product'].browse(product_id)
    #
    #         qty_sold = row['product_uom_qty']
    #
    #         velocity = qty_sold / days
    #
    #         results.append({
    #             'product_name': product.display_name,
    #             'qty_sold': qty_sold,
    #             'velocity': round(velocity, 2),
    #             'stock': product.qty_available,
    #         })
    #
    #     results.sort(
    #         key=lambda x: x['velocity'],
    #         reverse=True
    #     )
    #
    #     return results[:20]

    from collections import defaultdict
    from datetime import datetime

    def _get_restock_priority(self):
        domain = [
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', self.date_from),
            ('order_id.date_order', '<=', self.date_to),
            ('product_id.detailed_type', '=', 'product'),
        ]

        sale_lines = self.env['sale.order.line'].search(domain)

        # Calculate number of days in selected period
        date_from = datetime.strptime(str(self.date_from), "%Y-%m-%d")
        date_to = datetime.strptime(str(self.date_to), "%Y-%m-%d")

        total_days = (date_to - date_from).days + 1
        total_days = max(total_days, 1)

        products = defaultdict(lambda: {
            'qty_sold': 0.0,
            'revenue': 0.0,
        })
        # Merge all variants into the product template
        for line in sale_lines:
            tmpl = line.product_id.product_tmpl_id

            products[tmpl.id]['qty_sold'] += line.product_uom_qty
            products[tmpl.id]['revenue'] += line.price_subtotal

        result = []

        for tmpl_id, values in products.items():
            product = self.env['product.template'].browse(tmpl_id)

            qty_sold = values['qty_sold']
            revenue = values['revenue']

            avg_daily_sales = qty_sold / total_days

            # Total free stock across all variants
            current_stock = sum(product.product_variant_ids.mapped('free_qty'))

            if avg_daily_sales > 0:
                days_left = current_stock / avg_daily_sales
            else:
                days_left = 9999

            if days_left <= self.minimum_stock_days:
                status = 'Critical'
            elif days_left <= (self.minimum_stock_days * 2):
                status = 'Restock Soon'
            else:
                status = 'Healthy'

            result.append({
                'product_tmpl_id': product.id,
                'product_name': product.name,
                'qty_sold': round(qty_sold, 2),
                'revenue': round(revenue, 2),
                'avg_daily_sales': round(avg_daily_sales, 2),
                'current_stock': round(current_stock, 2),
                'days_left': round(days_left, 1),
                'status': status,
            })

        result = sorted(result, key=lambda x: x['days_left'])
        return {
            'summary': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'total_days': total_days,
                'critical_days': self.minimum_stock_days,
            },
            'products': result,
        }

    def _get_dead_stock(self):
        result = []

        products = self.env['product.template'].search([
            ('detailed_type', '=', 'product'),
        ])

        today = self.date_to
        total_stock_value = 0
        for product in products:

            current_stock = sum(product.product_variant_ids.mapped('free_qty'))

            if current_stock <= 0:
                continue

            last_order = self.env['sale.order'].search(
                [
                    ('state', 'in', ['sale', 'done']),
                    ('order_line.product_id.product_tmpl_id', '=', product.id),
                ],
                order='date_order desc',
                limit=1,
            )
            if last_order and last_order.date_order:
                last_sale_date = last_order.date_order.date()
                days_since_sale = (today - last_sale_date).days
            else:
                last_sale_date = False
                days_since_sale = 9999

            if days_since_sale < self.dead_stock_days:
                continue

            stock_value = current_stock * product.cost_for_reporting
            total_stock_value += stock_value
            cost = product.cost_for_reporting or 0.0
            result.append({
                'product_name': product.name,
                'current_stock': round(current_stock, 2),
                'last_sale_date': last_sale_date,
                'days_since_sale': days_since_sale,
                'cost': cost,
                'stock_value': round(stock_value, 2),
            })

        result = sorted(
            result,
            key=lambda x: x['days_since_sale'],
            reverse=True
        )

        return {
            'summary': {
                'dead_stock_days': self.dead_stock_days,
                'total_products': len(result),
                'total_stock_value': round(total_stock_value, 2),
            },
            'products': result,
        }

    from collections import defaultdict

    def _get_category_performance(self):
        domain = [
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', self.date_from),
            ('order_id.date_order', '<=', self.date_to),
            ('product_id.detailed_type', '=', 'product'),
        ]

        sale_lines = self.env['sale.order.line'].search(domain)

        categories = defaultdict(lambda: {
            'qty_sold': 0.0,
            'revenue': 0.0,
            'orders': 0,
        })

        for line in sale_lines:
            product = line.product_id.product_tmpl_id

            for category in product.public_categ_ids:
                categories[category.id]['name'] = category.name
                categories[category.id]['qty_sold'] += line.product_uom_qty
                categories[category.id]['revenue'] += line.price_subtotal
                categories[category.id]['orders'] += 1

        result = []

        total_revenue = sum(x['revenue'] for x in categories.values())

        for values in categories.values():
            avg_price = (
                values['revenue'] / values['qty_sold']
                if values['qty_sold'] else 0
            )

            contribution = (
                (values['revenue'] / total_revenue) * 100
                if total_revenue else 0
            )

            result.append({
                'category_name': values['name'],
                'revenue': round(values['revenue'], 2),
                'qty_sold': round(values['qty_sold'], 2),
                'orders': values['orders'],
                'avg_price': round(avg_price, 2),
                'contribution': round(contribution, 2),
            })

        result.sort(key=lambda x: x['revenue'], reverse=True)

        return {
            'summary': {
                'date_from': self.date_from,
                'date_to': self.date_to,
                'categories': len(result),
                'total_revenue': round(total_revenue, 2),
            },
            'rows': result,
        }

    def action_generate_pdf(self):
        data = {}

        if self.weekly_top_products:
            data['top_products'] = self._get_top_products()
        if self.top_category:
            data['category_performance'] = self._get_category_performance()

        # if self.fast_moving_products:
        #     data['fast_moving'] = self._get_fast_moving_products()


        if self.restock_priority:
            print(self._get_restock_priority())
            data['restock_priority'] = self._get_restock_priority()

        if self.dead_stock:
            data['dead_stock'] = self._get_dead_stock()

        return self.env.ref(
            'reporting.action_inventory_report'
        ).report_action(self, data=data)

class InventoryReport(models.AbstractModel):
    _name = 'report.reporting.inventory_report_template'

    def _get_report_values(self, docids, data=None):

        return {
            'doc_ids': docids,
            'doc_model': 'oyak.inventory.report.wizard',
            'docs': self.env[
                'oyak.inventory.report.wizard'
            ].browse(docids),
            'data': data or {},
        }