from odoo import models, fields


class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    is_controlled_product = fields.Boolean(string = "Es producto controlado", readonly = True)
    received_untaxed_price_total = fields.Float('Importe entregado', readonly = True)

    def _select(self):
        return super(PurchaseReport, self)._select() + ", t.is_controlled_product, sum(l.price_unit * l.qty_received / COALESCE(po.currency_rate, 1.0))::decimal(16,2) * currency_table.rate as received_untaxed_price_total"

    def _group_by(self):
        return super(PurchaseReport, self)._group_by() + ", t.is_controlled_product"
