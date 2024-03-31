from odoo import models, fields, api, _
import requests
import json
from odoo.exceptions import AccessError, UserError
import datetime
import logging

logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    payment_type = fields.Selection([
        ('cod', "COD"),
        ('Pre_paid', 'Pre-Paid'),
    ], string='Payment-Type')
    picking = fields.Char(string='Picking-ID')
    incoming_centre_name = fields.Char(string='Incoming Centre Name')
    pickup_location = fields.Char(string='Pickup Location')
    pickup_date = fields.Char(string='Pickup Date')
    waybill_no_data = fields.Char(string='Waybill-Barcode')
    order_id_data = fields.Char(string='Order ID-Barcode')
    cst_name = fields.Char(string='Customer Name')
    cst_address = fields.Char(string='Customer Address')
    cst_city = fields.Char(string='Customer City')
    cst_state = fields.Char(string='Customer State')
    cst_zip = fields.Char(string='Customer Pin')
    sname = fields.Char(string='Seller Name')
    sadd = fields.Char(string='Seller Address')
    pt = fields.Char(string='Payment Type')
    created_date = fields.Char(string='Date')
    r_name = fields.Char(string='Return Address', )
    r_add = fields.Char(string='Return Address', )
    r_cty = fields.Char(string='Return city')
    r_state = fields.Char(string='Return state')
    r_zip = fields.Char(string='Return Zip')
    status = fields.Char(string='Status')
    waybill = fields.Char(string='Waybill')
    remark = fields.Char(string='Remark')
    order_id = fields.Char(string='Order No')
    cancelled = fields.Boolean(string='Cancelled', default=False)
    created_by = fields.Many2one('res.users', 'Created By')
    cancelled_by = fields.Many2one('res.users', 'Cancelled By')
    cancelled_date = fields.Datetime('Cancellation Time')
    return_phone = fields.Char('Return Phone')
    return_diff = fields.Boolean('Return To Different Address ?', default=False)
    pickup_location_id = fields.Many2one('stock.location', 'Pickup Location')
    return_location_id = fields.Many2one('stock.location', 'Return Location')
    pickup_id = fields.Many2one('pickup.request', 'Pickup Request')
    # created_date = fields.Datetime('Created Date')
    current_status = fields.Char(string='Tracking Status')
    current_location = fields.Char(string='Current Location')
    expected_delivery_date = fields.Char(string='Expected Delivery Date')
    cancelled_waybill = fields.Boolean(default=True)
    msg_feedback = fields.Boolean(default=False)
    pickup_parent_id = fields.Many2one('stock.picking')
    daily_pickup_ids = fields.One2many('stock.picking', 'pickup_parent_id')

    # @api.onchange('picking_type_id')
    # def onchange_picking_address(self):
    #     if self.picking_type_id:
    #         warehouse = self.picking_type_id.warehouse_id
    #         self.r_add = warehouse.partner_id.street + ' ' + warehouse.partner_id.street2
    #         self.r_cty = warehouse.partner_id.city
    #         self.r_zip = warehouse.partner_id.zip
    #         self.r_state = warehouse.partner_id.state_id.name

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Shipped'),
        ('pro_recived', 'Delivered'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")

    # @api.depends('move_type', 'immediate_transfer', 'move_lines.state', 'move_lines.picking_id')
    # def _compute_state(self):
    #     ''' State of a picking depends on the state of its related stock.move
    #     - Draft: only used for "planned pickings"
    #     - Waiting: if the picking is not ready to be sent so if
    #       - (a) no quantity could be reserved at all or if
    #       - (b) some quantities could be reserved and the shipping policy is "deliver all at once"
    #     - Waiting another move: if the picking is waiting for another move
    #     - Ready: if the picking is ready to be sent so if:
    #       - (a) all quantities are reserved or if
    #       - (b) some quantities could be reserved and the shipping policy is "as soon as possible"
    #     - Done: if the picking is done.
    #     - Cancelled: if the picking is cancelled
    #     '''
    #     for picking in self:
    #         if not picking.move_lines:
    #             picking.state = 'draft'
    #         elif any(move.state == 'draft' for move in picking.move_lines):  # TDE FIXME: should be all ?
    #             picking.state = 'draft'
    #         elif all(move.state == 'cancel' for move in picking.move_lines):
    #             picking.state = 'cancel'
    #         elif all(move.state == 'pro_recived' for move in picking.move_lines):
    #             picking.state = 'pro_recived'
    #         elif all(move.state in ['cancel', 'done'] for move in picking.move_lines):
    #             picking.state = 'done'
    #         else:
    #             relevant_move_state = picking.move_lines._get_relevant_state_among_moves()
    #             if picking.immediate_transfer and relevant_move_state not in ('draft', 'cancel', 'done','pro_recived'):
    #                 picking.state = 'assigned'
    #             elif relevant_move_state == 'partially_available':
    #                 picking.state = 'assigned'
    #             else:
    #                 picking.state = relevant_move_state

    def print_slip(self):
        return self.env.ref('gts_delhivery_integration.report_waybill_slip').report_action(self)

    def create_delhivery_order(self):
        data = self.env['sale.order'].search([('name', '=', self.origin)], limit=1)
        total_amount = data.amount_total
        warehouse = self.picking_type_id.warehouse_id
        self.cancelled = False
        # function for register order with Delhivery
        if not warehouse.sync_with_delhivery:
            raise UserError(_('Please Sync Your Warehouse with Delhivary.'))
        if self.carrier_tracking_ref:
            raise UserError(_('Waybill Number is already generated for this Order'))
        if not self.payment_type:
            raise UserError(_('Payment Mode is Not Selected'))
        if not self.partner_id.street:
            raise UserError(_('Please Enter the street Address'))
        # if not self.partner_id.street2:
        #     raise UserError(_('Please Enter the street2 Address'))
        if not (self.partner_id.mobile or self.partner_id.phone):
            raise UserError(_('Please Enter Mobile Number'))
        if not self.partner_id.name:
            raise UserError(_('Please Enter Customer Name'))
        if not self.partner_id.zip:
            raise UserError(_('Please Enter Pincode'))
        if not self.origin:
            raise UserError(_('Delivery Order is not linked with Sales'))
        if not self.partner_id.city:
            raise UserError(_('Please Enter City Name'))
        if not warehouse.partner_id.state_id.name:
            raise UserError(_('State is not configured in Warehouse Please configure it'))
        if not warehouse.company_id.name:
            raise UserError(_('Company is not Mapped in Warehouse'))
        if not warehouse.partner_id.city:
            raise UserError(_('Origin City is not configured in Warehouse'))
        if not warehouse.partner_id.mobile:
            raise UserError(_('Please Enter Warehouse Mobile Number'))
        if not warehouse.partner_id.country_id.name:
            raise UserError(_('Please Enter Warehouse Country'))
        if not self.partner_id.state_id.name:
            raise UserError(_('Please Enter Customer State'))
        if not warehouse.partner_id.street:
            raise UserError(_('Please Enter Warehouse Address Street'))
        if not warehouse.partner_id.street2:
            raise UserError(_('Please Enter Warehouse Address Street2'))
        if not warehouse.partner_id.zip:
            raise UserError(_('Please Enter Warehouse Pincode'))
        if not warehouse.name:
            raise UserError(_('Please Enter Warehouse Name'))
        if not self.partner_id.country_id.name:
            raise UserError(_('Please Enter Customer Country'))

        weight = 0.0
        partner_name = self.partner_id.name
        partner_name = partner_name.replace('#', '').replace('%', '').replace('&', '').replace(';', '').replace('\\',
                                                                                                                '')
        partner_city = self.partner_id.city
        partner_city = partner_city.replace('#', '').replace('%', '').replace('&', '').replace(';', '').replace('\\',
                                                                                                                '')
        partner_street = self.partner_id.street
        partner_street = partner_street.replace('#', '').replace('%', '').replace('&', '').replace(';', '').replace(
            '\\', '')
        partner_street2 = self.partner_id.street2
        partner_street2 = partner_street2.replace('#', '').replace('%', '').replace('&', '').replace(';', '').replace(
            '\\', '')
        return_location_name = self.return_location_id.name
        return_location_name = return_location_name.replace('#', '').replace('%', '').replace('&', '').replace(';',
                                                                                                               '').replace(
            '\\', '')
        return_location_city = self.return_location_id.city
        return_location_city = return_location_city.replace('#', '').replace('%', '').replace('&', '').replace(';',
                                                                                                               '').replace(
            '\\', '')
        return_location_street = self.return_location_id.street
        return_location_street = return_location_street.replace('#', '').replace('%', '').replace('&', '').replace(';',
                                                                                                                   '').replace(
            '\\', '')
        return_location_street2 = self.return_location_id.street2
        return_location_street2 = return_location_street2.replace('#', '').replace('%', '').replace('&', '').replace(
            ';', '').replace('\\', '')
        pickup_location_name = self.pickup_location_id.name
        pickup_location_name = pickup_location_name.replace('#', '').replace('%', '').replace('&', '').replace(';',
                                                                                                               '').replace(
            '\\', '')
        pickup_location_city = self.pickup_location_id.city
        pickup_location_city = pickup_location_city.replace('#', '').replace('%', '').replace('&', '').replace(';',
                                                                                                               '').replace(
            '\\', '')
        pickup_location_street = self.pickup_location_id.street
        pickup_location_street = pickup_location_street.replace('#', '').replace('%', '').replace('&', '').replace(';',
                                                                                                                   '').replace(
            '\\', '')
        pickup_location_street2 = self.pickup_location_id.street2
        pickup_location_street2 = pickup_location_street2.replace('#', '').replace('%', '').replace('&', '').replace(
            ';', '').replace('\\', '')
        for item in self.move_ids_without_package:
            weight += item.product_id.weight * item.product_uom_qty
        phone = self.partner_id.mobile or self.partner_id.phone
        phone = phone.replace(' ', '')
        data = {
            "shipments": [{
                "add": partner_street + ' ' + partner_street2,
                'address_type': 'home',
                "phone": phone,
                "payment_mode": self.payment_type,
                "name": partner_name,
                "pin": self.partner_id.zip,
                "order": self.origin,
                "seller_gst_tin":self.company_id and self.company_id.vat,
                # 'client_gst_tin': self.partner_id.vat,
                "city": partner_city,
                "state": self.partner_id.state_id.name,

                "return_state": self.return_location_id.state_id.name,
                "seller_name": warehouse.company_id.name,
                "return_city": return_location_city,
                "return_phone": self.return_location_id.phone,
                "return_country": self.return_location_id.country_id.name,

                # "order_date": self.scheduled_date,
                "return_add": return_location_street + ' ' + return_location_street2,
                "total_amount": total_amount,
                "seller_add": pickup_location_street + ' ' + pickup_location_street2,
                "country": self.pickup_location_id.country_id.name,
                "return_pin": self.return_location_id.zip,
                "return_name": return_location_name,
            }],
            "pickup_location": {
                "name": pickup_location_name,
                "city": pickup_location_city,
                "pin": self.pickup_location_id.zip,
                "country": self.pickup_location_id.country_id.name,
                "state": self.pickup_location_id.state_id.name,
                "phone": self.pickup_location_id.phone,
                "add": pickup_location_street + ' ' + pickup_location_street2
            }
        }
        if self.payment_type == 'cod':
            data["shipments"][0].update({"cod_amount": total_amount})
        if weight:
            data["shipments"][0].update({'weight': weight})

        payload = "format=json&data={}".format(str(data).replace("'", '"'))
        configuration = self.env['delivery.configuration'].search([], limit=1)
        if configuration.request_type == 'test':
            url = configuration.create_order_test
            api = 'Token' + ' ' + configuration.test_api
        elif configuration.request_type == 'production':
            url = configuration.create_order_Production
            api = 'Token' + ' ' + configuration.production_api
        headers = {'Authorization': api,
                   'Content-Type': 'application/json'}
        logger.info("=========waybill API Data====%s====", payload)
        print(data,"asd")
        print(payload,"asd")
        response = requests.post(url, data=payload, headers=headers)

        res = response.content
        res_dic = json.loads(res.decode('utf-8'))
        logger.info("=========waybill Response====%s====", res_dic)
        success = False
        for key in res_dic.get('packages'):
            self.write({
                'carrier_tracking_ref': key.get('waybill'),
                'waybill': key.get('waybill'),
                'created_by': self.env.user.id,
                'status': 'Generated'
                # 'created_date': datetime.datetime.now()
            })
            success = True
            # self.env.user.notify_danger(message='Hi %s, \n \n We are happy to inform you that your order is ready, shipped, and on its way to you! You know what this means- you will soon own an original, unique, and handcrafted product, made with love by the women of Shilpgram \n \n Your order will be delivered by our logistics partner Delhivery. You can track your shipment [link] with tracking No: %s \n \n If you have any questions for us, just hit reply and our team will be happy to help you.' % (self.partner_id.name, key.get('waybill')))
            # notification = _('Hi %s, \n \n We are happy to inform you that your order is ready, shipped, and on its way to you! You know what this means- you will soon own an original, unique, and handcrafted product, made with love by the women of Shilpgram \n \n Your order will be delivered by our logistics partner Delhivery. You can track your shipment [link] with tracking No: %s \n \n If you have any questions for us, just hit reply and our team will be happy to help you.' % (self.partner_id.name, key.get('waybill')))
            subject = 'Your Shilpgram order is %s on its way to you!' % (self.origin)
            html = """
                <!DOCTYPE html>
                <html>
                <head>
                <meta charset=\"utf-8\" />
                </head>
                <body>
                Hi %s,<br/><br/>
                We are happy to inform you that your order is ready, shipped, and on its way to you! You know what this means- you will soon own an original, unique, OYAK product, made with love by Team OYAK
                <br/><br/>
                You can track your shipment with tracking No: %s 
                <br/><br/>
                If you have any questions for us, just hit reply and our team will be happy to help you.
                <br/><br/>
                <div class="s_share" data-name="Share">
                    # <h4 class="s_share_title">Follow us </h4>
                    # <a href="https://www.facebook.com/ShilpgramBRLPS" target="_blank">
                    #   <img src="https://img.icons8.com/fluency/30/000000/facebook-new.png"/>
                    # </a>
                    # <a href="https://twitter.com/shilpgram_brlps">
                    #   <img src="https://img.icons8.com/color/30/000000/twitter.png"/>
                    # </a>
                    <a href="https://www.instagram.com/oyak_clothing/">
                      <img src="https://img.icons8.com/color/30/000000/instagram-new.png"/>
                    </a>
                </div>
                </body></html>
                """ % (self.partner_id.name, key.get('waybill'))

        if not success:
            raise UserError(_('Could not Generate Delivery Slip due to Technical Error'))
        self.message_post(body=html, message_type="notification", subtype_id=self.env.ref('mail.mt_comment').id,
                          subject=subject)
        self.generate_slip()

    @api.model
    def create(self, vals_list):
        res = super(StockPicking, self).create(vals_list)
        pick_location_id = self.env['stock.location'].search([('is_pickup', '=', True),
                                                              ('is_default', '=', True)], limit=1)
        dest_location_id = self.env['stock.location'].search([('return_location', '=', True),
                                                              ('is_default', '=', True)], limit=1)
        if pick_location_id:
            res.pickup_location_id = pick_location_id.id
            res.return_location_id = pick_location_id.id
        if dest_location_id:
            res.return_location_id = dest_location_id.id
        return res

    def generate_slip(self):
        # function for generate pdf slip(Package slip)
        if not self.carrier_tracking_ref:
            raise UserError(_('Waybill No Not Found. Please verify and Generate it in-order to Generate Pickup'))
        waybill = self.carrier_tracking_ref
        configuration = self.env['delivery.configuration'].search([], limit=1)
        if configuration.request_type == 'test':
            url = configuration.slip_generate_test_url
            api = configuration.test_api
        elif configuration.request_type == 'production':
            url = configuration.slip_generate_Production_url
            api = configuration.production_api
        else:
            raise UserError(_('No Configuration Found !! Please verify Delhivary Configuration.'))
        headers = {'Authorization': 'Token' + ' ' + api}
        response = requests.get(url + waybill, headers=headers)
        res = response.content
        df1 = json.loads(res.decode('utf-8'))
        for key in df1['packages']:
            self.write({
                'created_date': key.get('cd'),
                'cst_name': key.get('name'),
                'cst_address': key.get('address'),
                'cst_city': key.get('destination_city'),
                'cst_state': key.get('customer_state'),
                'cst_zip': key.get('pin'),
                'sname': key.get('snm'),
                'sadd': key.get('sadd'),
                'waybill_no_data': key.get('barcode'),
                'order_id_data': key.get('oid_barcode'),
                # 'r_add': key.get('radd'),
                # 'r_cty': key.get('rcty'),
                # 'r_state': key.get('rst'),
                # 'r_zip': key.get('rpin'),
                'pt': key.get('pt'),
            })

    def convert_string_to_byte(self):
        barcode_waybill = str.encode(self.waybill_no_data)
        return barcode_waybill

    def convert_string_oid_byte(self):
        oid = str.encode(self.order_id_data)
        return oid

    def order_tracking(self):
        if not self.carrier_tracking_ref:
            raise UserError(_('Waybill no is not generated yet'))
        configuration = self.env['delivery.configuration'].search([], limit=1)
        client_action = {
            'type': 'ir.actions.act_url',
            'name': "Shipment Tracking Page",
            'target': 'new',
            'url': configuration.order_tracking_url,
        }
        return client_action

    def order_cancel(self):
        from lxml import objectify
        # function is used for cancel order
        if not self.carrier_tracking_ref:
            raise UserError(_('No Active Order Found ! '))
        data = {
            "waybill": self.carrier_tracking_ref,
            "cancellation": "true"

        }
        configuration = self.env['delivery.configuration'].search([], limit=1)
        if configuration.request_type == 'test':
            url = configuration.cancel_order_test
            api_token = configuration.test_api
        elif configuration.request_type == 'production':
            url = configuration.cancel_order_production
            api_token = configuration.production_api
        else:
            raise UserError(_('Please Check configuration details (or) Something went Wrong.'))
        headers = {'Authorization': 'Token' + ' ' + api_token, 'Content-Type': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        res = response.content
        df = res.decode('utf-8')
        xml_string = df.replace('<?xml version="1.0" encoding="utf-8"?>\n', '')
        xml_object = objectify.fromstring(xml_string)
        xml_dict = xml_object.__dict__
        self.write({
            # 'status': xml_dict.get('status'),
            'waybill': xml_dict.get('waybill'),
            'remark': xml_dict.get('remark'),
            'order_id': xml_dict.get('order_id'),
            'cancelled': True,
            'status': 'Cancelled',
            'carrier_tracking_ref': False,
            'cancelled_by': self.env.user.id,
            'cancelled_date': datetime.datetime.now()
        })
        self.env.user.notify_danger(
            message='Remark: %s And Order-No is: %s' % (xml_dict.get('remark'), (xml_dict.get('order_id'))))

    def recive_by_customer(self):
        order_picking = self.env['stock.picking'].search(
            [('waybill', '!=', False), ('current_status', '!=', 'Delivered')])
        configuration = self.env['delivery.configuration'].search([], limit=1)
        # staging
        if configuration.request_type == 'test':
            url = configuration.test_tracking_url
            api_token = configuration.test_api

        elif configuration.request_type == 'production':
            url = configuration.production_tracking_url
            api_token = configuration.production_api

        headers = {'Authorization': 'Token' + ' ' + api_token}
        for picking in order_picking:
            data = {
                "waybill": picking.waybill,
                "token": api_token
            }
            try:
                response = requests.get(url, params=data, headers=headers)
                res = response.content
                res_dic = json.loads(res.decode('utf-8'))
            except Exception:
                pass
            if res_dic.get('ShipmentData'):
                for shipment in res_dic.get('ShipmentData'):
                    picking.current_status = shipment.get('Shipment').get('Status').get('Status')
                    picking.current_location = shipment.get('Shipment').get('Status').get('StatusLocation')
                    picking.expected_delivery_date = shipment.get('Shipment').get('ExpectedDeliveryDate')
                    picking.cancelled_waybill = False
            order = self.env['sale.order'].search([('id', '=', picking.id)], limit=1)
            if picking.current_status == 'Delivered' and picking.msg_feedback == False:
                picking.state = 'pro_recived'
                template = picking.env.ref('gts_email.mail_template_feedback')
                template.sudo().with_context().send_mail(order.id, force_send=True)
                picking.msg_feedback = True

    def get_order_track(self):
        configuration = self.env['delivery.configuration'].search([], limit=1)
        # staging
        if configuration.request_type == 'test':
            url = configuration.test_tracking_url
            api_token = configuration.test_api

        elif configuration.request_type == 'production':
            url = configuration.production_tracking_url
            api_token = configuration.production_api

            data = {
                "waybill": self.waybill,
                "token": api_token
            }
            if self.current_status == 'Delivered':
                self.env.user.notify_danger(message='Order is Successfully Delivered')
            else:
                headers = {'Authorization': 'Token' + ' ' + api_token}
                response = requests.get(url, params=data, headers=headers)
                print(response)
                res = response.content
                print(res)
                res_dic = json.loads(res.decode('utf-8'))
                if (res_dic.get('ShipmentData') and self.current_status != 'Delivered'):
                    for shipment in res_dic.get('ShipmentData'):
                        self.current_status = shipment.get('Shipment').get('Status').get('Status')
                        self.current_location = shipment.get('Shipment').get('Status').get('StatusLocation')
                        self.expected_delivery_date = shipment.get('Shipment').get('ExpectedDeliveryDate')
                if self.current_status == 'Delivered':
                    self.state = 'pro_recived'

    # def send_picking_status(self):
    #     picking_state_ids = self.env['stock.picking'].search([('state','in', ('waiting', 'confirmed' 'draft', 'assigned'))])
    # print("==================================>>>>>>>>>>>>>>>",picking_state_ids)
    # self.daily_pickup_ids = [(6, 0, picking_state_ids)]
    # print("==================================>>>>>>>>>>>>>>>",self.daily_pickup_ids)
    # for picking in picking_state_ids:


class ReportWaybill(models.AbstractModel):
    _name = "report.gts_delhivery_integration.report_waybill_slip"

    def _get_report_values(self, docids, data=None):
        docs = self.env['stock.picking'].browse(docids)
        if not docs.waybill:
            raise AccessError(_('You Can not print Slip if Waybill is not Generated !'))
        if docs.cancelled:
            raise AccessError(_('You Can not print Slip for cancelled order !'))

        return {
            'doc_ids': docs.ids,
            'doc_model': 'stock.picking',
            'docs': docs,
        }

# class StockMove(models.Model):
#     _inherit = 'stock.move'


#     def send_picking_status(self):
#         picking_state_ids = self.env['stock.picking'].search([('state','in', ('waiting', 'confirmed' 'draft', 'assigned'))])
