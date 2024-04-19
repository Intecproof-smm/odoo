from odoo import models, fields


class ResUsers(models.Model):
    _inherit = 'res.users'

    x_ignorar_restriccion_default_branch = fields.Boolean(string = 'Ignorar restricción default branch', store = True)
    x_validar_salidas = fields.Boolean(string = 'Validar salidas de inventario manual', store = True)
