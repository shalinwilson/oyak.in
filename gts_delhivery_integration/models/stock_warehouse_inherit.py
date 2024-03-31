from odoo import models, fields, api, _
import requests
from odoo.exceptions import AccessError, UserError
import json
import logging
_logger = logging.getLogger(__name__)

class StockWarehouse(models.Model):
    _inherit = ['stock.warehouse', 'mail.thread', 'mail.activity.mixin']
    _name = 'stock.warehouse'
    # _inherit = ['mail.thread','mail.activity.mixin']

    sync_with_delhivery = fields.Boolean(string="Sync With Delhivery", track_visibility='onchange')
    delhivery_credential_id = fields.Many2one('delivery.configuration', string="Delhivery Configuration")

    def register_warehouse_with_delhivery(self):
        # function for sinking warehouse with delhivery

        if not self.partner_id.mobile:
            raise UserError(_('Please Enter Mobile Number'))
        if not self.partner_id.city:
            raise UserError(_('Please Enter City'))
        if not self.name:
            raise UserError(_('Please Enter Name'))
        if not self.partner_id.zip:
            raise UserError(_('Please Enter Pincode'))
        if not self.partner_id.country_id.name:
            raise UserError(_('Please Enter Country Name'))
        if not self.partner_id.email:
            raise UserError(_('Please Enter Email-Id'))
        if self.sync_with_delhivery:
            raise UserError(_('Warehouse is already created with Delhivery'))
        data = {
            "phone": self.partner_id.mobile,
            "city": self.partner_id.city,
            "name": self.name,
            "pin": self.partner_id.zip,
            "address": self.partner_id.street + self.partner_id.street2,
            "country": self.partner_id.country_id.name,
            "email": self.partner_id.email,
            "return_address": self.partner_id.street + self.partner_id.street2,
            "return_pin": self.partner_id.zip,
            "return_city": self.partner_id.city,
            "return_state": self.partner_id.state_id.name,
            "return_country": self.partner_id.country_id.name
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
        print(res)
        res_dict = json.loads(res.decode('utf-8'))
        print(res_dict)

        error_code_list = res_dict.get('error_code')
        if 'error_code' not in res_dict.keys():
            _logger.info('Warehouse Created Successfully')
            self.sync_with_delhivery = True
        elif 'error_code' in res_dict.keys():
            if error_code_list[0] == 2000:
                # self.env.user.notify_danger(message='Warehouse id already Created with Delhivery')
                _logger.info('Warehouse id already Created with Delhivery')

                self.sync_with_delhivery = True
            else:
                _logger.info('please fill all details correctly.')

        else:
            raise UserError(_('Something went Wrong. Please Contact to admin. Thank you'))
