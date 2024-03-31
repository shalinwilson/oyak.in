from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
import logging
_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    payment_type = fields.Selection([
        ('cod', "COD"),
        ('Pre_paid', 'Pre-Paid'),
    ], string='Payment-Type')

    def _prepare_procurement_values(self):
        values = super(StockMove, self)._prepare_procurement_values()
        values.update({
            'payment_type': self.payment_type,
        })
        return values

    def _get_new_picking_values(self):
        values = super(StockMove, self)._get_new_picking_values()
        for move in self:
            values.update({
                'payment_type': move.payment_type,
            })
        return values

    result = []

    def send_picking_status(self):
        users_list = self.env.user.search([])
        picking_state_ids = self.env['stock.picking'].search([('state','in', ('waiting', 'confirmed' 'draft', 'assigned'))])
        email_subject = 'Daily Picking Status Email'
        order_id = ""
        for picking in picking_state_ids:
            picking.move_ids_without_package
            for pick in picking:
                for line in pick.move_ids_without_package:
                    order_id += "<tr>" + "<td width=""15%"">" +  (line.origin) + "<td width=""15%"">" +  (line.partner_id.name) +  "<td width=""50%"">" +  (line.product_id.name) +  "<td width=""10%"">" +  (str(line.product_uom_qty)) +  "<td width=""10%"">" +  (str(line.quantity_done))
        status_table = " <p> Hello, </p>    <p> Today’s Padding Picking Status Reports: </p> <br/>   <table border="" 1px solid black""> <tr> <th width=""20%""> Sale Order </th>    <th width=""20%""> Customer </th> <th width=""50%""> Product </th> <th width=""10%""> Order </th> <th width=""10%""> Shipped </th> {0} </tr> </table>".format(order_id)
        # for group_user in users_list:
        #     if group_user.has_group('gts_delhivery_integration.group_user_sale_report'):
        #         mail={
        #               'subject'    : email_subject,
        #               'email_from' : 'admin@brlps.in',
        #               'email_to'   :  group_user.login,
        #               'body_html'  : status_table
        #              }
        #         mail_create = self.env['mail.mail'].create(mail)
        #         mail_create.send()



class Location(models.Model):
    _inherit = "stock.location"

    def _get_country(self):
        country = self.env['res.country'].search([('name','=','India')])
        return country

    is_pickup = fields.Boolean("Is Pickup Location")
    code = fields.Char('Location Code')
    is_default = fields.Boolean('Default Location')
    phone = fields.Char('Phone')
    email = fields.Char('Email')
    street = fields.Char('Street')
    street2 = fields.Char('Street 2')
    city = fields.Char('City')
    zip = fields.Char('Zip')
    state_id = fields.Many2one('res.country.state', 'State')
    country_id = fields.Many2one('res.country','Country',default=_get_country)
    is_sync = fields.Boolean('Synced ')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Location Code must be Unique'),
    ]


    def write(self, vals):
        res = super(Location, self).write(vals)
        if vals.get('is_default'):
            if self.is_pickup and self.return_location:
                old_ids = self.search([('is_default','=', True),('id','!=',self.id)])
            elif self.is_pickup and not self.return_location:
                old_ids = self.search([('is_default', '=', True),('is_pickup','=',True),('id','!=',self.id)])
            elif self.return_location and not self.is_pickup:
                old_ids = self.search([('is_default', '=', True), ('return_location', '=', True),('id','!=',self.id)])
            if old_ids:
                self.env.cr.execute("update stock_location set is_default = False where id in %s",
                                    (tuple(old_ids.ids,),))
        return res


    def register_location(self):
        # function for sinking warehouse with delhivery

        if not self.phone:
            raise UserError(_('Please Enter Mobile Number'))
        if not self.city:
            raise UserError(_('Please Enter City'))
        if not self.name:
            raise UserError(_('Please Enter Name'))
        if not self.zip:
            raise UserError(_('Please Enter Pincode'))
        if not self.country_id.name:
            raise UserError(_('Please Enter Country Name'))
        if not self.email:
            raise UserError(_('Please Enter Email-Id'))
        if self.is_sync:
            raise UserError(_('Warehouse is already created with Delhivery'))
        data = {
            "phone": self.phone,
            "city": self.city,
            "name": self.name,
            "pin": self.zip,
            "address": self.street + self.street2,
            "country": self.country_id.name,
            "email": self.email,
            "return_address": self.street + self.street2,
            "return_pin": self.zip,
            "return_city": self.city,
            "return_state": self.state_id.name,
            "return_country": self.country_id.name
        }
        configuration = self.env['delivery.configuration'].search([], limit=1)
        if configuration.request_type == 'test':
            data.update({"registered_name": configuration.test_client})
            url = configuration.warehouse_sinking_test_url
            Token = 'Token ' + configuration.test_api

        elif configuration.request_type == 'production':
            data.update({"registered_name": configuration.production_client})
            url = configuration.warehouse_Production_url
            Token = 'Token ' + configuration.production_api
        else:
            raise UserError(_('Please check configuration details.'))

        headers = {'Authorization': Token,
                   'Content-Type': 'application/json', 'Accept': 'application/json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)
        res = response.content
        res_dict = json.loads(res.decode('utf-8'))
        error_code_list = res_dict.get('error_code')
        if 'error_code' not in res_dict.keys():
            print('Location Created Successfully')
            _logger.info("loc created")
            self.is_sync = True
        elif 'error_code' in res_dict.keys():
            if error_code_list[0] == 2000:
                _logger.info("Location id already Created with Delhiver")

                # self.env.user.notify_danger(message='Location id already Created with Delhivery')
                self.sync_with_delhivery = True
            else:
                _logger.info("please fill all details correctly.")
                # self.env.user.notify_danger(message='please fill all details correctly.')
        else:
            raise UserError(_('Something went Wrong. Please Contact to admin. Thank you'))





