from odoo import models, fields


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    x_descripcion = fields.Char(string = 'Descripcin', store = True)
