import requests
import json
from odoo import api, models, fields
import logging
# access_token = "EAAQWu3WK82gBP0mUWYqClvnCEnwClaSM71nnSvM55bby1ZCmxbeM2ebS9cLlVn5mOO8EqEcSSRyyjJRaZCEAPNDzkZA7Fs07S4K0sXq7LcAbJ77N7b4WkySXzGYvoySBw4a72EqzY8MgOLmPDx4wwtIUw3A6AjN6sbPY461zYavPkCtd668PMnmbXpIAhnrE4PSGv33m2dqrYvYxUtVzwYKZBT9Ntq5LHdKWrDr3tTHCwp8NBZAgIaIe7J0PcFu8kOgGIwh3XCpZAEyfLfPcSfZCeeM"
# access_token = "EAAQWu3WK82gBP1NLAZB32VI5ScxxNp9p2atXABGZA6s9cY62MfNYBUzGk7jDlLLcfLrNsczEUAAomMKRdoaPQZBFnvFYWVwHN2vxZCGEZA0nj6tSCRBMejK7TTFyPxWaGLA80tEdveWyzohdeyaHOjcFgyK6y47FNqJMvItem03vobfIv1PJceM9m1a7NUvTUEgZDZD"
access_token = "EAAQWu3WK82gBP5HZBI0arEjKxIyd108jUv4SESpJ74ZCWADFNefEzDAP7F11n615W19YDuT6r4TeFfQU6timn4Us4u38qyGZAkMlISKu7Kaw8UTGjsd4zZA36e6nCUchb6vAPuYAfolwGlsAixynGAuZBPuB2YLxlcNPezqC4PnocktB8vbeZCKMYWJiwnBDlu7wZDZD"
phone_number_id = "814431681743532"
_logger = logging.getLogger(__name__)



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    whatsapp_message_id = fields.Char(string="WhatsApp Message ID")
    latest_confirmed_so = fields.Boolean()
    def make_proper_num(self):
        self.ensure_one()
        mobile = self.partner_mobile
        mobile = mobile.replace(" ", "").replace("+", "")
        self.partner_mobile = mobile
    def get_whatsapp_number(self):
        self.ensure_one()
        mobile = self.partner_mobile
        mobile = mobile.replace(" ", "").replace("+", "")
        if len(mobile) == 10 and mobile.isdigit():
            mobile = "91" + mobile
        return mobile

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.send_whatsapp_confirmation()
        return res

    def remove_old_so_communication_flag(self):
        mobile = self.partner_mobile
        orders = self.env["sale.order"].search([('partner_mobile', 'ilike', mobile),('state','=','sale')])
        for rec in orders:
            rec.latest_confirmed_so = False

    def get_order_line_short_text(self):
        items = []
        for line in self.order_line:
            if not line.display_type:
                items.append(f"{line.product_id.display_name} {int(line.product_uom_qty)} qty")
        return ", ".join(items)

    def send_whatsapp_confirmation(self):
        for order in self:
            print("sending whatsapp message ",order)
            # Prepare payload with NAMED parameters
            payload = {
                "messaging_product": "whatsapp",
                "to": order.get_whatsapp_number(),
                "type": "template",
                "template": {
                    "name": "order_confirmation",  # template name in Meta
                    "language": {"code": "en"},
                    "components": [
                        {
                            "type": "HEADER",
                            "parameters": [
                                {
                                    "type": "text",
                                    "parameter_name": "order",
                                    "text": order.name
                                }
                            ],
                        },
                        {
                            "type": "body",
                            "parameters": [
                                {
                                    "type": "text",
                                    "parameter_name": "customer_name",
                                    "text": order.partner_id.name
                                },
                                {
                                    "type": "text",
                                    "parameter_name": "order_id",
                                    "text": order.name
                                },
                                {
                                    "type": "text",
                                    "parameter_name": "item_list",
                                    "text": order.get_order_line_short_text()
                                },
                                {
                                    "type": "text",
                                    "parameter_name": "order_total",
                                    "text": str(round(order.amount_total))
                                }
                            ]
                        },
                    ],
                },
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"

            response = requests.post(url, headers=headers, json=payload)
            print(response)
            try:
                response_json = response.json()
            except ValueError:
                _logger.error("Invalid JSON response: %s", response.text)
                return
            message_id = response_json.get('messages', [{}])[0].get('id')
            if message_id:
                order.whatsapp_message_id = message_id
                order.remove_old_so_communication_flag()
                order.latest_confirmed_so = True
                order.message_post(
                    body=f"📤 WhatsApp sent to {order.partner_id.name}<br/>"
                         f"Status Code: {response.status_code}<br/>"
                         f"Response: {response.text}")

    def send_whatsapp_reply(self, text):
        for order in self:
            if not order.partner_mobile:
                _logger.warning("No mobile number found for order %s", order.name)
                continue
            order.make_proper_num()
            url = f"https://graph.facebook.com/v20.0/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "to": order.get_whatsapp_number(),
                "context": {"message_id": order.whatsapp_message_id},  # Reply in same thread
                "type": "text",
                "text": {"body": text}
            }

            response = requests.post(url, headers=headers, json=payload)
            order.message_post(
                body=f"📤 WhatsApp sent to {order.partner_id.name}<br/>"
                     f"Status Code: {response.status_code}<br/>"
                     f"Response: {response.text}")
            _logger.info("📤 WhatsApp reply sent for %s\nResponse: %s", order.name, response.text)


