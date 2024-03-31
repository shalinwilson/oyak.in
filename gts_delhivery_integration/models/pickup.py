from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import requests
from datetime import timedelta, datetime


class Pickup(models.Model):
    _name='pickup.request'

    name = fields.Char('Pickup Name')
    package_count = fields.Integer('Package Count', default=1)
    picking_ids = fields.Many2many('stock.picking', string='Pickings')
    pickup_date = fields.Datetime('Pickup Datetime')
    location_id = fields.Many2one('stock.location','Pickup Location')
    center = fields.Char('Center Name')
    pickup_code = fields.Char('Pickup Code')
    state = fields.Selection([('draft','Draft'),('schedule','Scheduled')],'Status', default='draft')


    @api.onchange('pickup_date')
    def onchange_pickup(self):
        if self.pickup_date:
            date = datetime.now()
            if self.pickup_date < date:
                # UserError(_('Pickup time Can not be less that current time'))
                warning_mess = {
                'title': _('Wrong Time!'),
                'message': _("Pickup time Can not be less that current time")

                }
                return {'warning': warning_mess}



    def request_pickup(self):
        if self.pickup_date < datetime.now():
            UserError(_('Pickup time Can not be less that current time'))
        date1 = self.pickup_date.strftime('%Y-%m-%d 00:00:01')
        date2 = self.pickup_date.strftime('%Y-%m-%d 23:59:59')
        old_ids = self.search([('pickup_date','>=',date1),('pickup_date','<=',date2),('location_id','=',self.location_id.id),
                               ('state','=','schedule')])
        if old_ids:
            raise UserError(_('Pickup request of %s for %s is already exist') % (self.location_id.name, date1))
        if not self.package_count:
            raise UserError(_('Please Enter the package Count'))
        if not self.pickup_date:
            raise UserError(_('Please Enter Date and Time'))
        if not self.location_id:
            raise UserError(_('Please Select Pickup Location.'))
        date_time = self.pickup_date
        date = '{:%Y-%m-%d}'.format(date_time)
        correct_time = self.pickup_date + timedelta(hours=5, minutes=35)
        time = '{:%H:%M:%S}'.format(correct_time)
        data = {
            "pickup_time": time,
            "pickup_date": date,
            "pickup_location": self.location_id.name,
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
        print ("response====",res)
        df = json.loads(res.decode('utf-8'))
        if df.get('pr_exist',False):
            message = df.get('data',{}).get('message', '')
            raise UserError (_('%s')%(message))
        if not df.get('incoming_center_name'):
            raise UserError (_('Something Went Wrong'))
        self.write({
            'center': df.get('incoming_center_name'),
            'pickup_code': df.get('pickup_id')
        })
        for picking in self.picking_ids:
            picking.write({
                'picking': df.get('pickup_id'),
                'incoming_centre_name': df.get('incoming_center_name'),
                'pickup_location': df.get('pickup_location_name'),
                'pickup_date': df.get('pickup_date'),
            })
        self.state = 'schedule'

        self.env.user.notify_danger(
            message='Pickup Location is : %s  Incoming Centre Name : %s Pickup Date is : %s' % (
                df.get('pickup_id'), df.get('incoming_center_name'), df.get('pickup_date')))

