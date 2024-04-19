from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_fecha_nacimiento = fields.Date(string = 'Fecha de nacimiento', store = True)
    x_id_tarjeta = fields.Char(string = 'ID Tarjeta', store = True)
