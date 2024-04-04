from odoo import models, fields, api, _
class ResCountry(models.Model):
    _inherit = 'res.country'


    def get_website_sale_states(self, mode='billing'):
        res = super(ResCountry, self).get_website_sale_states(mode=mode)
        print("working")
        states = self.env['res.country.state']
        if mode == 'shipping':
            dom = ['|', ('country_ids', 'in', self.id), ('country_ids', '=', False), ('website_published', '=', True)]
            delivery_carriers = self.env['delivery.carrier'].sudo().search(dom)

            for carrier in delivery_carriers:
                if not carrier.country_ids or not carrier.state_ids:
                    states = res
                    break
                states |= carrier.state_ids
            if not states:
                states = states.search([('country_id', '=', self.id),('code','=','KL')])
            res = res & states
        return res.filtered(lambda x:x.code == 'KL')


