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
		dominio_comun = [
			('quant_ids.quantity', '>', '0'),
			('quant_ids.location_id', '=', id_location),
			('quant_ids.location_id.x_stock_location', '=', True)
		]
		dominio_vencidos = [
			('expiration_date', '!=', None),
			('expiration_date', '<', fields.date.today().strftime('%Y-%m-%d 00:00:00'))
		]
		dominio_hoy = [
			('expiration_date', '>=', fields.date.today().strftime('%Y-%m-%d 00:00:00')),
			('expiration_date', '<=', fields.date.today() + relativedelta(days=15))
		]
		dominio_proximos = [
			('expiration_date', '>=', fields.date.today() + relativedelta(days=16)),
			('expiration_date', '<=', fields.date.today() + relativedelta(days=30))
		]
		dominio_ok = [
			('expiration_date', '>=', fields.date.today() + relativedelta(days=61)),
			('expiration_date', '<=', fields.date.today() + relativedelta(days=90))
		]
		# ToDo ----- Aquí tenemos que poner el campo agrupador de la ubicación -----
		contexto = "{'group_by':'x_categoria', 'order':'expiration_date'}"
		dominio_vencidos += dominio_comun
		dominio_hoy += dominio_comun
		dominio_proximos += dominio_comun
		dominio_ok += dominio_comun
		
		total_medicamentos_vencidos = self.env['stock.lot'].search(dominio_vencidos)
		total_medicamentos_hoy_vencen = self.env['stock.lot'].search(dominio_hoy)
		total_medicamentos_proximos_a_vencer = self.env['stock.lot'].search(dominio_proximos)
		total_medicamentos_ok = self.env['stock.lot'].search(dominio_ok)
		return {
			'total_medicamentos_vencidos': len(total_medicamentos_vencidos),
			'total_medicamentos_hoy_vencen': len(total_medicamentos_hoy_vencen),
			'total_medicamentos_proximos_a_vencer': len(total_medicamentos_proximos_a_vencer),
			'total_medicamentos_ok': len(total_medicamentos_ok),
			'dominio_vencidos': dominio_vencidos,
			'dominio_hoy': dominio_hoy,
			'dominio_proximos': dominio_proximos,
			'dominio_ok': dominio_ok,
			'context': contexto
		}
	
	@api.model
	def traer_location_data(self):
		location = self.env['stock.location'].search([('x_branch', '=', self.env.user.branch_id.id)])
		return location.id
	
	# ----------------------------------------------------------
	# Basea de datos
	# ----------------------------------------------------------
	x_categoria = fields.Char(related='product_id.categ_id.name', string='Categoría', store=True)
	x_ubicacion = fields.Char(compute='traer_ubicacion_stock_move', string='Ubicación', store=False)
	x_product_qty = fields.Float('Quantity', compute='_x_product_qty', precompute='_x_product_qty')
	
	@api.model
	def traer_ubicacion_stock_move(self):
		for rec in self:
			rec.x_ubicacion = self.env['res.branch'].search([('id', '=', self.env.user.branch_id.id)]).name

	@api.depends('quant_ids', 'quant_ids.quantity')
	def _x_product_qty(self):
		for lot in self:
			# We only care for the quants in internal or transit locations.
			if not self.env.user.x_ignorar_restriccion_default_branch:
				quants = lot.quant_ids.filtered(lambda q: q.location_id.id == self.traer_location_data())
			else:
				quants = lot.quant_ids.filtered(lambda q: q.location_id.x_stock_location)
			
			lot.x_product_qty = sum(quants.mapped('quantity'))
