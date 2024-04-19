from odoo import api, fields, models
from datetime import date


class StockProductionLot(models.Model):
    _inherit = 'stock.lot'
    _order = 'expiration_date asc' #ordena lista de lotes por fecha de expiracion

    location_ids = fields.Many2many(comodel_name = 'stock.location'
                                        ,compute = '_compute_location_ids'
                                        , store = True)

    @api.depends('quant_ids', 'quant_ids.location_id')
    def _compute_location_ids(self):
        for lot in self:
            lot.location_ids = lot.quant_ids.filtered(lambda l: l.quantity > 0).mapped('location_id')

    #concatenar nombre de lote y fecha de expiracion
    def name_get(self):
        res = []
        for lot in self:
            lot_data = lot.name or ""
            if lot.expiration_date:
                lot_data += " / " + str(lot.expiration_date.date()) or ""
            res.append((lot.id, lot_data))
        return res
