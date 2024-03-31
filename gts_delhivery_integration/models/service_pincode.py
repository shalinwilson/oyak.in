from odoo import models, fields, api, _


class ServicePincode(models.Model):
    _name = 'service.pincode'

    name = fields.Char()
    district = fields.Char()
    country_id = fields.Many2one('res.country')
    state_id = fields.Many2one('res.country.state')
    max_amount = fields.Float()
    pre_paid = fields.Char()
    cash = fields.Char()
    pickup = fields.Char()
    cod = fields.Char()

