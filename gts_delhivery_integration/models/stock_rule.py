from odoo import models, fields, api, _


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['payment_type']
        return fields

    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        new_move_vals = super(StockRule, self)._push_prepare_move_copy_values(
            move_to_copy, new_date)
        new_move_vals.update({
            'payment_type': move_to_copy.payment_type,
        })
        return new_move_vals
