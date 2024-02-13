# -*- coding: utf-8 -*-
from odoo import models, fields

# Clase que extiende el objeto de sesión para cargar propiedades
# adicionales de los productos, así como registrar el turno en
# el que opera la sesión
class PosSession(models.Model):
    _inherit = 'pos.session'

    x_turno = fields.Selection(
        selection = [
            ('m', 'M')
            , ('v', 'V')
            , ('n1', 'N1')
            , ('n2', 'N2')
            , ('ja', 'JA')
            , ('jf', 'JF')
        ]
        , string = 'Turno'
        , store = True
    )

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('is_controlled_product')
        return result
    
    def _loader_params_pos_payment_method(self):
        params = super()._loader_params_pos_payment_method()
        params["search_params"]["fields"].extend(
            ["vevent_payment_terminal_mode", "vevent_payment_terminal_id"]
        )
        return params

    def _loader_params_pos_session(self):
        result = super()._loader_params_pos_session()
        result['search_params']['fields'].append('x_turno')
        return result