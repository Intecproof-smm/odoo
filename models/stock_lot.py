# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (c) 2023-today Juan Carlos Flores.
#
#    This file is part of SMM_intecproof Module
#
#    This program is NOT a free software
#
###################################################################################
from dateutil.relativedelta import relativedelta
from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class ExtendStock_lot(models.Model):
	_inherit = 'stock.lot'

	# ----------------------------------------------------------
	# Definiciones de funciones
	# ----------------------------------------------------------

	@api.model
	def get_medicamentos_data(self):
		total_medicamentos_vencidos = self.env['stock.lot'].search([('product_id.categ_id.name', '=', 'Medicamentos'), ('quant_ids.quantity', '>', '0'), ('expiration_date', '<', fields.date.today())])
		total_medicamentos_hoy_vencen = self.env['stock.lot'].search([('product_id.categ_id.name', '=', 'Medicamentos'), ('quant_ids.quantity', '>', '0'), ('expiration_date', '>=', fields.date.today().strftime('%Y-%m-%d 00:00:00')), ('expiration_date', '<=', fields.date.today().strftime('%Y-%m-%d 23:59:59'))])
		total_medicamentos_proximos_a_vencer = self.env['stock.lot'].search([('product_id.categ_id.name', '=', 'Medicamentos'), ('quant_ids.quantity', '>', '0'), ('expiration_date', '>=', fields.date.today()+relativedelta(days=1)), ('expiration_date', '<=', fields.date.today()+relativedelta(months=1))])
		total_medicamentos_ok = self.env['stock.lot'].search([('product_id.categ_id.name', '=', 'Medicamentos'), ('quant_ids.quantity', '>', '0'), ('expiration_date', '>', fields.date.today()+relativedelta(months=1))])
		return {
			'total_medicamentos_vencidos': len(total_medicamentos_vencidos),
			'total_medicamentos_hoy_vencen': len(total_medicamentos_hoy_vencen),
			'total_medicamentos_proximos_a_vencer': len(total_medicamentos_proximos_a_vencer),
			'total_medicamentos_ok': len(total_medicamentos_ok)
		}

	def get_lots_expiring(self):
		expiring_lots = self.env['stock.lot'].search([
			('product_id.categ_id.name', '=', 'Medicamentos'), ('quant_ids.quantity', '>', '0'),
			('expiration_date', '<', fields.date.today())
		])
		return expiring_lots
	
	def open_expiring_lots_view(self):
		expiring_lots = self.get_lots_expiring()
		action = {
			'name': 'Expiring_Lots',
			'type': 'ir.actions.act_window',
			'res_model': 'stock.lot',
			'view_mode': 'tree,form',
			'domain': [('id', 'in', expiring_lots.ids)],
		}
		return action
	
	def get_lots_expiring_today(self):
		expiring_lots_today = self.env['stock.lot'].search([
			('product_id.categ_id.name', '=', 'Medicamentos'), ('quant_ids.quantity', '>', '0'),
			('expiration_date', '>=', fields.date.today().strftime('%Y-%m-%d 00:00:00')),
			('expiration_date', '<=', fields.date.today().strftime('%Y-%m-%d 23:59:59'))
		])
		return expiring_lots_today
	
	def open_expiring_lots_today_view(self):
		expiring_lots_today = self.get_lots_expiring_today()
		action = {
			'name': 'Expiring_Lots_Today',
			'type': 'ir.actions.act_window',
			'res_model': 'stock.lot',
			'view_mode': 'tree,form',
			'domain': [('id', 'in', expiring_lots_today.ids)],
		}
		return action
	
	def get_lots_expiring_soon(self):
		expiring_lots_soon = self.env['stock.lot'].search([
			('product_id.categ_id.name', '=', 'Medicamentos'), ('quant_ids.quantity', '>', '0'),
			('expiration_date', '>=', fields.date.today() + relativedelta(days=1)),
			('expiration_date', '<=', fields.date.today() + relativedelta(months=1))
		])
		return expiring_lots_soon
	
	def open_expiring_lots_soon_view(self):
		expiring_lots_soon = self.get_lots_expiring_soon()
		action = {
			'name': 'Expiring_Lots_soon',
			'type': 'ir.actions.act_window',
			'res_model': 'stock.lot',
			'view_mode': 'tree,form',
			'domain': [('id', 'in', expiring_lots_soon.ids)],
		}
		return action
	
	def get_lots_expiring_ok(self):
		expiring_lots_ok = total_medicamentos_ok = self.env['stock.lot'].search([
			('product_id.categ_id.name', '=', 'Medicamentos'), ('quant_ids.quantity', '>', '0'),
			('expiration_date', '>', fields.date.today() + relativedelta(months=1))
		])
		return expiring_lots_ok
	
	def open_expiring_lots_ok_view(self):
		expiring_lots_ok = self.get_lots_expiring_ok()
		action = {
			'name': 'Expiring_Lots_current',
			'type': 'ir.actions.act_window',
			'res_model': 'stock.lot',
			'view_mode': 'tree,form',
			'domain': [('id', 'in', expiring_lots_ok.ids)],
		}
		return action
	