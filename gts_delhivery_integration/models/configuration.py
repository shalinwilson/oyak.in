from odoo.addons.account_check_printing.models.res_company import res_company
from odoo import models, fields, api, _
import requests
import json
from odoo.exceptions import AccessError, UserError


class DeliveryConfiguration(models.Model):
    _name = 'delivery.configuration'
    _rec_name = 'request_type'

    request_type = fields.Selection([
        ('test', 'Test'),
        ('production', 'Production')
    ], string='Select Request')

    # testing credentials
    order_tracking_url = fields.Char('Order Tracking Url')
    test_api = fields.Char(string='API Token')
    pincode_test_url = fields.Char(string='Pincode Url', default='https://staging-express.delhivery.com/c/api/pin-codes/json')
    warehouse_sinking_test_url = fields.Char(string='Warehouse Url', default='https://staging-express.delhivery.com/c/api/pin-codes/json')
    create_order_test = fields.Char(string='Order Creation Url', default='https://staging-express.delhivery.com/api/cmu/create.json')
    slip_generate_test_url = fields.Char(string='Slip Creation Url', default='https://staging-express.delhivery.com/api/p/packing_slip')
    test_pickup_api_url = fields.Char(string='Package Pickup Url', default='https://staging-express.delhivery.com/fm/request/new')
    order_tracking_test_url = fields.Char(string='Order Tracking Url', default='https://staging-express.delhivery.com/api/v1/packages')
    # test_waybill_fetch = fields.Char(string='Waybill Url')
    test_client = fields.Char('Client')
    cancel_order_test = fields.Char(string='Cancel Order Url', default='https://staging-express.delhivery.com/api/p/edit')
    test_tracking_url = fields.Char(string='Tracking Url', default='https://staging-express.delhivery.com/api/v1/packages')
    # test_Pickup = fields.Char(string='Pickup/Warehouse')


    # production credentials
    production_api = fields.Char(string='API Token')
    pincode_Production_url = fields.Char(string='Pincode Url',default='https://track.delhivery.com/c/api/pin-codes/json')
    warehouse_Production_url = fields.Char(string='Warehouse Url' , default='https://track.delhivery.com/c/api/pin-codes/json')
    create_order_Production = fields.Char(string='Order Creation Url', default='https://track.delhivery.com/api/cmu/create.json')
    slip_generate_Production_url = fields.Char(string='Slip Creation Url',default='https://track.delhivery.com/api/p/packing_slip')
    production_pickup_api_url = fields.Char(string='Package Pickup Url',  default='https://track.delhivery.com/fm/request/new')
    order_tracking_production_url = fields.Char(string='Order Tracking Url',default='https://track.delhivery.com/api/v1/packages')
    cancel_order_production = fields.Char(string='Cancel Order Url',  default='https://track.delhivery.com/api/p/edit')
    production_client = fields.Char('Client')
    production_tracking_url = fields.Char(string='Tracking Url', default='https://track.delhivery.com/api/v1/packages')

    def get_pincode(self):
        headers={}
        self.env['service.pincode'].search([]).unlink()
        configuration = self.env['delivery.configuration'].search([], limit=1)
        if configuration.request_type == 'test':
            url = configuration.pincode_test_url
            headers = {
                "accept": "application/json",
                "Authorization": configuration.test_api,
            }

        elif configuration.request_type == 'production':
            url = configuration.pincode_Production_url
            headers = {
                "accept": "application/json",
                "Authorization": configuration.production_api
            }

        else:
            raise UserError(_('Please Verify Pin-code Api and Url Again'))
            # response = requests.get(url)
            # if response.status_code == 200:

        print(url,headers)
        response = requests.get(url,headers=headers)
        print(response)
        dict_content = response.content
        data = json.loads(dict_content)
        for key in data['delivery_codes']:
            state_code = key.get('postal_code', {}).get('state_code')
            country_code = key.get('postal_code', {}).get('country_code')
            state = self.env['res.country.state'].search(
                [('code', '=', state_code), ('country_id.code', '=', country_code)], limit=1)
            country = self.env['res.country'].search([('code', '=', country_code)], limit=1)
            self.env['service.pincode'].create({
                'name': key.get('postal_code', {}).get('pin'),
                'district': key.get('postal_code', {}).get('district'),
                'country_id': country.id if country else False,
                'state_id': state.id if state else False,
                # 'covid_zone': key.get('postal_code', {}).get('covid_zone'),
                'max_amount': key.get('postal_code', {}).get('max_amount'),
                'pre_paid': key.get('postal_code', {}).get('pre_paid'),
                'cash': key.get('postal_code', {}).get('cash'),
                'pickup': key.get('postal_code', {}).get('pickup'),
                'cod': key.get('postal_code', {}).get('cod'),
            })
