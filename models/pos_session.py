# -*- coding: utf-8 -*-
from odoo import models

# Clase que extiende el objeto de sesión para cargar propiedades
# adicionales de los productos
class PosSession(models.Model):
    _inherit = 'pos.session'

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
