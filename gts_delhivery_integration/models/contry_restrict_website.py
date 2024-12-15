from odoo import models, fields, api, _
class ResCountry(models.Model):
    _inherit = 'res.country'

    def get_website_sale_countries(self, mode='billing'):
        res = super(ResCountry, self).get_website_sale_countries(mode=mode)
        print("original")
        if mode == 'shipping':
            countries = self.env['res.country']

            delivery_carriers = self.env['delivery.carrier'].sudo().search([('website_published', '=', True)])
            for carrier in delivery_carriers:
                if not carrier.country_ids and not carrier.state_ids:
                    countries = res
                    break
                countries |= carrier.country_ids
            print(res & countries)
            res = res & countries
        return res.filtered(lambda x:x.code in ['IN'])

    def get_website_sale_states(self, mode='billing'):
        res = super(ResCountry, self).get_website_sale_states(mode=mode)
        print("working 1")
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
                states = states.search([('country_id', '=', self.id),('code','in',['TN','KA','KL'])])

            print(states,"Asd")
            res = res & states
            print(res & states,"states")
        return res.filtered(lambda x:x.code in ['KL','TN','KA'])


