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
		id_location = self.traer_location_data()
		total_medicamentos_vencidos = self.env['stock.lot'].search([
			('expiration_date', '!=', None),
			('quant_ids.quantity', '>', '0'),
			('expiration_date', '<', fields.date.today()),
			('quant_ids.location_id', '=', id_location)
		])
		total_medicamentos_hoy_vencen = self.env['stock.lot'].search([
			('quant_ids.quantity', '>', '0'),
			('expiration_date', '>=', fields.date.today().strftime('%Y-%m-%d 00:00:00')),
			('expiration_date', '<=', fields.date.today().strftime('%Y-%m-%d 23:59:59')),
			('quant_ids.location_id', '=', id_location)
		])
		total_medicamentos_proximos_a_vencer = self.env['stock.lot'].search([
			('quant_ids.quantity', '>', '0'),
			('expiration_date', '>=', fields.date.today()+relativedelta(days=1)),
			('expiration_date', '<=', fields.date.today()+relativedelta(months=1)),
			('quant_ids.location_id', '=', id_location)
		])
		total_medicamentos_ok = self.env['stock.lot'].search([
			('quant_ids.quantity', '>', '0'),
			('expiration_date', '>', fields.date.today()+relativedelta(months=1)),
			('quant_ids.location_id', '=', id_location)
		])
		return {
			'total_medicamentos_vencidos': len(total_medicamentos_vencidos),
			'total_medicamentos_hoy_vencen': len(total_medicamentos_hoy_vencen),
			'total_medicamentos_proximos_a_vencer': len(total_medicamentos_proximos_a_vencer),
			'total_medicamentos_ok': len(total_medicamentos_ok)
		}

	@api.model
	def traer_location_data(self):
		location = self.env['stock.location'].search([('x_branch', '=', self.env.user.branch_id.id)])
		_logger.info("El resultado de location.id es : " + str(location.id))
		return location.id
	
	# ----------------------------------------------------------
	# Basea de datos
	# ----------------------------------------------------------
	x_categoria = fields.Char(related='product_id.categ_id.name', string='Categoría', store=True)
	x_ubicacion = fields.Char(compute='traer_ubicacion_stock_move', string='Ubicación', store=False)
	x_product_qty = fields.Float('Quantity', compute='_x_product_qty')
	
	@api.model
	def traer_ubicacion_stock_move(self):
		for rec in self:
			rec.x_ubicacion = self.env['res.branch'].search([('id', '=', self.env.user.branch_id.id)]).name

	@api.depends('quant_ids', 'quant_ids.quantity')
	def _x_product_qty(self):
		for lot in self:
			# We only care for the quants in internal or transit locations.
			quants = lot.quant_ids.filtered(lambda q: q.location_id.id == self.traer_location_data())
			lot.x_product_qty = sum(quants.mapped('quantity'))
