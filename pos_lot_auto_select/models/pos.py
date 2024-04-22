from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare

from itertools import groupby
from datetime import datetime, date, timedelta
import logging

_logger = logging.getLogger(__name__)

class pos_config(models.Model):
	_inherit = 'pos.config'

	allow_pos_lot = fields.Boolean('Allow POS Lot/Serial Number', default=True)
	allow_auto_select_lot = fields.Boolean('Allow Auto select Lot/Serial Number', default=True)
	lot_expire_days = fields.Integer('Product Lot/Serial expire days.', default=1)
	pos_lot_receipt = fields.Boolean('Print Lot/Serial on receipt',default=1)

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	allow_pos_lot = fields.Boolean(related='pos_config_id.allow_pos_lot', readonly=False, string='Allow POS Lot/Serial Number')
	allow_auto_select_lot = fields.Boolean(related='pos_config_id.allow_auto_select_lot', readonly=False, string='Allow Auto select Lot/Serial Number')
	lot_expire_days = fields.Integer(related='pos_config_id.lot_expire_days', readonly=False, string='Product Lot/Serial expire days.')
	pos_lot_receipt = fields.Boolean(related='pos_config_id.pos_lot_receipt', readonly=False, string='Print Lot/Serial on receipt')

class account_move_line(models.Model):
	_inherit = 'account.move.line'

	lot_ids = fields.Many2many('stock.lot',string="Lots")
	pos_lot_ids = fields.Many2many('pos.pack.operation.lot',string="POS Lots")


class PosSession(models.Model):
	_inherit = 'pos.session'

	@api.model
	def _pos_ui_models_to_load(self):
		res = super(PosSession, self)._pos_ui_models_to_load()
		res.append('stock.lot')
		res.append('stock.quant')
		res.append('pos.pack.operation.lot')
		return res

	def _loader_params_stock_quant(self):
		fields = ['id','product_id','quantity','location_id','lot_id']
		location_id = self.config_id.picking_type_id.default_location_src_id
		domain = [('location_id', '=', location_id.id)]
		return {'search_params': {'domain': domain, 'fields': fields}}

	def _get_pos_ui_stock_quant(self,params):
		result  = self.env['stock.quant'].search_read(**params['search_params'])
		list_lot_stock_quant = []
		for stock in result:
			list_lot_stock_quant.append(stock)
		final_result = {
			'list_lot_stock_quant':list_lot_stock_quant,
		}
		return final_result		

	def _loader_params_stock_lot(self):
		fields = ['id','name','product_id','product_qty','total_available_qty','product_uom_id','expiration_date']
		domain = [('id','=',0)]
		if self.config_id.allow_pos_lot:
			domain = []
		return {'search_params': {'domain': domain, 'fields': fields}}

	def _get_pos_ui_stock_lot(self,params):
		result  = self.env['stock.lot'].search_read(**params['search_params'])
		list_lot_num = []
		list_lot_num_by_id = {}
		list_lot_num_by_product_id = {}
		from_lot_expire_days = fields.Datetime.now() + timedelta(days = self.config_id.lot_expire_days)

		for lot in result:
			product = False
			if lot['product_id']:
				product = self.env['product.product'].browse(lot['product_id'][0])

			if product and product.use_expiration_date:
				if not lot['expiration_date'] or lot['expiration_date']>from_lot_expire_days:
					list_lot_num.append(lot)
			else:
					list_lot_num.append(lot)
			if lot['total_available_qty']>0:
				list_lot_num_by_id[lot['id']] = lot
				if lot['product_id'][0] in list_lot_num_by_product_id:
					list_lot_num_by_product_id[lot['product_id'][0]].append(lot)
				else:
					list_lot_num_by_product_id[lot['product_id'][0]] = []
					list_lot_num_by_product_id[lot['product_id'][0]].append(lot)
		final_result = {
			'list_lot_num':list_lot_num,
			'list_lot_num_by_id':list_lot_num_by_id,
			'list_lot_num_by_product_id':list_lot_num_by_product_id
		}
		return final_result

	def _loader_params_pos_pack_operation_lot(self):
		fields = ['id','pos_order_line_id', 'lot_name']
		domain = []
		return {'search_params': {'domain': domain, 'fields': fields}}

	def _get_pos_ui_pos_pack_operation_lot(self,params):
		result  = self.env['pos.pack.operation.lot'].search_read(**params['search_params'])
		pos_pack_lot_by_line_id = {}
		for pack_lot in result:
			if pack_lot.get('pos_order_line_id'):
				if pack_lot['pos_order_line_id'][0] in pos_pack_lot_by_line_id:
					pos_pack_lot_by_line_id[pack_lot['pos_order_line_id'][0]].append(pack_lot)
				else:
					pos_pack_lot_by_line_id[pack_lot['pos_order_line_id'][0]] = []
					pos_pack_lot_by_line_id[pack_lot['pos_order_line_id'][0]].append(pack_lot)
		return pos_pack_lot_by_line_id



class pos_order(models.Model):
	_inherit = 'pos.order'

	def _prepare_invoice_line(self, order_line):
		res  = super(pos_order, self)._prepare_invoice_line(order_line)
		lots = order_line.pack_lot_ids.mapped('lot_name')
		lot_rec = self.env['stock.lot'].search([('name','in',lots)])
		res.update({
			'lot_ids': [(6, 0, lot_rec.ids)],
			'pos_lot_ids' : [(6, 0, order_line.pack_lot_ids.ids)],
		})
		return res


class stock_lot(models.Model):
	_inherit = "stock.lot"

	total_available_qty = fields.Float("Total Qty", compute="_computeTotalAvailableQty")

	def _computeTotalAvailableQty(self):
		for record in self:
			move_line = self.env['stock.move.line'].search([('lot_id','=',record.id)])
			record.total_available_qty = 0.0
			for rec in move_line:
				if rec.location_dest_id.usage in ['internal', 'transit']:
					record.total_available_qty += rec.qty_done
				else:
					record.total_available_qty -= rec.qty_done


class pos_stock_quant(models.Model):
	_name = "pos.stock.quant"

	name = fields.Char()


	@api.model
	def valid_lot_by_location_pos(self, product_id, pos_id):
		pos_config = self.env['pos.config'].browse(pos_id)

		valid = 0
		if product_id != None:
			location_id = pos_config.picking_type_id.default_location_src_id
			stock_quants = self.env['stock.quant'].search(['&', ('location_id', '=', location_id.id), ('product_id', '=', product_id.get('product_id')[0])])
			_logger.info('stock_quants --->>>  ' + str(len(stock_quants)) + '  -  ' + location_id.name)
			for stock_quant in stock_quants:
				_logger.info('stock_quant --->>>  ' + str(stock_quant.lot_id.name) + '  -  ' +  str(product_id.get('product_id')[0]))
				_logger.info('stock_quant --->>>  ' + str(stock_quant) + '  -  ' +  str(product_id.get('product_id')[0]))
				if stock_quant.lot_id.name == product_id.get('name'):
					valid = 1
				else:
					valid = 0
		return {
				'product_qty': 10, 
				'location_id': pos_config.warehouse_id.lot_stock_id, 
				'valid': valid}