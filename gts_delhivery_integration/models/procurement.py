from odoo import models, fields, api, _


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    payment_type = fields.Selection([
        ('cod', "COD"),
        ('Pre_paid', 'Pre-Paid'),
    ], string='Payment-Type')

    def _prepare_procurement_values(self):
        values = super(ProcurementGroup, self)._prepare_procurement_values()
        values.update({
            'payment_type': self.payment_type,
        })
        return values
