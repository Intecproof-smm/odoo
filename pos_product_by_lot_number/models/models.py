# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class StockProductionLot(models.Model):
    _inherit = "stock.lot"

    @api.model
    def check_lot_by_rpc(self, data):
        lot = self.search([("name","=",data.get("name")),("product_id","=",data.get("product_id"))])
        if lot:
            return True
  
class EnableSettings(models.TransientModel):
    _inherit = "res.config.settings"

    @api.model
    def enable_lot_setting(self):
        enable_setting = self.create(dict(group_stock_production_lot = True))
        enable_setting.execute()

class ActionValidateInventory(models.Model):
    _inherit = "stock.quant"

    @api.model
    def validate_inventory(self):
        inventory = self.env.ref('pos_product_by_lot_number.stock_inventory_demo')
        validate = inventory.action_validate()

class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        model_stock_lot = "stock.lot"
        if model_stock_lot not in result:
            result.append(model_stock_lot)
        return result

    def _get_pos_ui_stock_lot(self, params):
        return self.env['stock.lot'].search_read(**params['search_params'])

    def _loader_params_stock_lot(self):
        model_fields = ['name', 'product_id', 'product_qty', 'id']
        return {'search_params': {'domain': [], 'fields': model_fields}}