from odoo import models, fields, api, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def generar_presupuesto(self):
        self.env['purchase.order.budget.wizard']._generar_presupuesto()
