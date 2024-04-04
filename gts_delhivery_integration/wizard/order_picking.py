from odoo import models, fields, api, _
import requests
import json
from odoo.exceptions import AccessError, UserError
# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT,  pytz, timedelta, datetime
from datetime import datetime
from datetime import date, datetime, timedelta


class OrderPicking(models.TransientModel):
    _name = 'package.picking'

    package_count = fields.Integer(string='Package Count', default=1)
    pickup_date = fields.Datetime(string='Date', default=fields.Datetime.now)
    pickup_location = fields.Many2one('stock.warehouse', string='Pickup Location')
    picking_id = fields.Many2one('stock.picking', string='Picking Id')

    @api.model
    def default_get(self, fields):
        record_ids = self._context.get('active_ids')
        result = super(OrderPicking, self).default_get(fields)
        result['picking_id'] = record_ids[0]
        return result

    def picking_order_confirm(self):
        if not self.package_count:
            raise UserError(_('Please Enter the package Count'))
        if not self.pickup_date:
            raise UserError(_('Please Enter Date and Time'))
        if not self.pickup_location:
            raise UserError(_('Please Select Pickup Location.'))
        date_time = self.pickup_date
        date = '{:%Y-%m-%d}'.format(date_time)
        correct_time = self.pickup_date + datetime.timedelta(hours=5, minutes=35)
        time = '{:%H:%M:%S}'.format(correct_time)
        data = {
            "pickup_time": time,
            "pickup_date": date,
            "pickup_location": self.pickup_location.name,
            "expected_package_count": self.package_count
        }
        data = json.dumps(data)
        configuration = self.env['delivery.configuration'].search([], limit=1)

        # staging
        if configuration.request_type == 'test':
            url = configuration.test_pickup_api_url
            api_token = configuration.test_api

        elif configuration.request_type == 'production':
            url = configuration.production_pickup_api_url
            api_token = configuration.production_api

        headers = {'Authorization': 'Token' + ' ' + api_token, 'Content-Type': 'application/json'}
        response = requests.post(url, data=data, headers=headers)
        res = response.content
        df = json.loads(res.decode('utf-8'))
        self.picking_id.update({
            'picking': df.get('pickup_id'),
            'incoming_centre_name': df.get('incoming_center_name'),
            'pickup_location': df.get('pickup_location_name'),
            'pickup_date': df.get('pickup_date'),
        })
        self.env.user.notify_danger(message='Pickup Location is : %s  Incoming Centre Name : %s Pickup Date is : %s' % (
        df.get('pickup_id'), df.get('incoming_center_name'), df.get('pickup_date')))
