
import json
import logging
access_token = "EAAQWu3WK82gBP5HZBI0arEjKxIyd108jUv4SESpJ74ZCWADFNefEzDAP7F11n615W19YDuT6r4TeFfQU6timn4Us4u38qyGZAkMlISKu7Kaw8UTGjsd4zZA36e6nCUchb6vAPuYAfolwGlsAixynGAuZBPuB2YLxlcNPezqC4PnocktB8vbeZCKMYWJiwnBDlu7wZDZD"
phone_number_id = "814431681743532"
import requests

from odoo import http,_
from odoo.http import request, Response
import builtins


_logger = logging.getLogger(__name__)

class WhatsAppWebhookController(http.Controller):
    VERIFY_TOKEN = "oyak_whatsapp_tokenx"

    @http.route('/webhook/whatsapp', type='http', auth='public', methods=['GET', 'POST'], csrf=False)
    def whatsapp_webhook(self, **kwargs):
        # --- STEP 1: Verify token during setup ---
        _logger.info("working working =====================g")
        _logger.info(str(kwargs))
        _logger.info(kwargs)
        _logger.info("kwargs")
        raw_body = request.httprequest.data
        _logger.info(f"🧾 Raw body: {raw_body}")
        if request.httprequest.method == 'GET':
            mode = kwargs.get('hub.mode')
            token = kwargs.get('hub.verify_token')
            challenge = kwargs.get('hub.challenge')

            if mode == 'subscribe' and token == self.VERIFY_TOKEN:
                return Response(challenge, status=200)
            else:
                return Response("Verification failed", status=403)

        # --- STEP 2: Handle incoming messages ---
        if request.httprequest.method == 'POST':
            _logger.info("===================== POST received")
            try:
                raw_data = request.httprequest.data  # bytes
                if not raw_data:
                    return Response("No data", status=400)

                _logger.info(f"🧾 Raw data post: {raw_data}")

                # Decode + load JSON
                data = json.loads(raw_data.decode('utf-8'))
                _logger.info(f"Parsed JSON: {data}")

                # Extract required fields safely
                entry = data.get('entry', [{}])[0]
                changes = entry.get('changes', [{}])[0]
                value = changes.get('value', {})
                messages = value.get('messages', [])
                contacts = value.get('contacts', [])

                if not messages:
                    return Response("No messages found", status=200)

                msg = messages[0]
                name = "Customer"
                if contacts:
                    contact = contacts[0]
                    name = contact.get('profile', {}).get('name')
                msg_id = msg.get('context', {}).get('id')
                reply_text = msg.get('button', {}).get('text')
                normal_text = msg.get('text', {}).get('body')
                _logger.info(f"msg_id={msg_id}, reply_text={reply_text}")
                _logger.info(f"msg_id={msg_id}, normal_text={normal_text}")
                if msg_id:
                    order = request.env['sale.order'].sudo().search([('whatsapp_message_id', '=', msg_id)], limit=1)
                else:
                    from_number = msg.get('from')
                    without91 = from_number[2:]
                    _logger.info(f"from number: {from_number}")
                    order = request.env['sale.order'].sudo().search([
                        ('partner_mobile', 'ilike', from_number),
                        ('latest_confirmed_so', '=', True),
                        ('state', '=', 'sale'),
                    ],)
                    if not order:
                        _logger.info(f"from 2nd number: {without91}")
                        order = request.env['sale.order'].sudo().search([
                            ('partner_mobile', 'ilike', without91),
                            ('latest_confirmed_so', '=', True),
                            ('state', '=', 'sale'),
                        ], )

                    _logger.info(f"Found order: {order}")

                if order:
                    text = reply_text or normal_text
                    _logger.info(f"Posting to chatter text=‘{text}’ len={len(text) if text else 0}")
                    order.message_post(body=f"📩 Customer replied: {text}")
                    # order.message_post(body=normal_text)
                    if text == "Confirm & get tracking":
                        _logger.info("✅ Generate delivery slip here")
                        order.call_detail = 'waauto'
                        try:
                            order.make_delhivery_order()
                        except:
                            pass
                        # tracking_url = "https://www.delhivery.com/track-v2/package/"+order.tracking_number
                        # if order.tracking_number:
                        #     text = "Your order has been shipped! 🚚 Track here:"+tracking_url+" You can track your package using this number. Thank you for shopping with OYAK."
                        # else:
                        #     text = "We will manually ship it and inform you details over mail and whatsapp"
                        # order.send_whatsapp_reply(text)
                    elif text == "Cancel":
                        _logger.info("✅ Customer initiated cancel")
                        order.call_detail = 'cancel'
                        if order.payment_type == 'cod':
                            if not order.tracking_number:
                                order.action_cancel()
                        text = "We will be cancelling it if its a COD order, If its paid we will call and confirm Cancel and refund"
                        order.send_whatsapp_reply(text)
                else:
                    _logger.info(name)

                    #     TODO: send common msg
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": from_number,
                        "type": "template",
                        "template": {
                            "name": "enquiry",  # template name in Meta
                            "language": {"code": "en"},
                            "components": [
                                {
                                    "type": "body",
                                    "parameters": [
                                        {
                                            "type": "text",
                                            "parameter_name": "customer_name",
                                            "text": name
                                        },
                                        {
                                            "type": "text",
                                            "parameter_name": "first_message",
                                            "text": "Please make an Order in our website www.oyak.in , We havent found any recent orders from your mobile number"

                                        },
                                    ]
                                },


                            ]}}

                    print(payload)

                    headers = {
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    }

                    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"

                    response = requests.post(url, headers=headers, json=payload)
                    print(response.json())



                return Response("Message processed", status=200)

            except Exception as e:
                _logger.exception("Error processing WhatsApp message:")
                return Response(f"Error: {str(e)}", status=500)
