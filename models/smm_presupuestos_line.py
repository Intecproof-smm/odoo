# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (c) 2024-today Juan Carlos Flores.
#
#    This file is part of SMM_intecproof Module
#
#    This program is NOT a free software
#
###################################################################################
import pkg_resources

from odoo import models, fields, api
from dateutil import relativedelta
import dateutil
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class PresupuestosDetalle(models.Model):
	_name = 'smm_presupuestos_line'
	_description = 'Detalle del presupuesto de compra y consumo de productos en unidades'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	
	# ----------------------------------------------------------
	# Base de datos
	# ----------------------------------------------------------
	presupuesto_id = fields.Many2one(
		comodel_name='smm_presupuestos',
		autojoin=True,
		string='Presupuesto'
	)
	product_id = fields.Many2one(
		comodel_name='product.product',
		string='Producto',
		required=True,
		tracking=True
	)
	cantidad = fields.Float(default='1', required=True, tracking=True)
	cantidad_consumida_periodo = fields.Float(
		compute='_traer_cantidad_consumida',
		store=False,
		string='Periodo actual'
	)
	cantidad_consumida_periodo_anterior = fields.Float(
		compute='_traer_cantidad_consumida_anterior',
		store=False,
		string='Periodo anterior'
	)
	cantidad_consumida_ano_anterior = fields.Float(
		compute='_traer_cantidad_consumida_ano_anterior',
		store=False,
		string='Año anterior'
	)

	@api.model
	def _traer_cantidad_consumida(self):
		# Traer la ubicación del almacén General
		ubicacion = self.env['stock.location'].search([('complete_name', '=', 'SMM-G/Existencias')], limit=1)
		# Traer los datos de la partida para regresar el consumo
		for rec in self:
			filtro = [
				('date', '>=', rec.presupuesto_id.fecha_inicial),
				('date', '<=', rec.presupuesto_id.fecha_final),
				('product_category_name', '=', rec.presupuesto_id.categoria.complete_name),
				('product_id', '=', rec.product_id.id),
				('state', '=', 'done'),
				('location_id', '=', ubicacion.id),
				('location_dest_id', '=', rec.presupuesto_id.ubicacion_id.id)
			]
			cantidad = 0
			partidas = self.env['stock.move.line'].search(filtro)
			for p in partidas:
				cantidad += p.qty_done
			rec.cantidad_consumida_periodo = cantidad

	@api.model
	def _traer_cantidad_consumida_anterior(self):
		for rec in self:
			# Calcular el lapso de tiempo que hay entre las 2 fechas en meses y años
			lapso_meses = (int(rec.presupuesto_id.mes_final) - int(rec.presupuesto_id.mes_inicial)) + 1
			lapso_anos = rec.presupuesto_id.ano_final - rec.presupuesto_id.ano_inicial
			# Calcular la fecha inicial del periodo anterior
			if int(rec.presupuesto_id.mes_inicial) <= lapso_meses:
				lm = lapso_meses - (int(rec.presupuesto_id.mes_inicial) - 1)
				mes_inicial = 13 - lm
				ano_inicial = rec.presupuesto_id.ano_inicial - (lapso_anos + 1)
			else:
				mes_inicial = int(rec.presupuesto_id.mes_inicial) - lapso_meses
				ano_inicial = int(rec.presupuesto_id.ano_inicial) - lapso_anos
			fecha_inicial = datetime(ano_inicial, mes_inicial, 1)
			# Calcular la fecha final del periodo anterior
			if int(rec.presupuesto_id.mes_final) <= lapso_meses:
				lm = lapso_meses - (int(rec.presupuesto_id.mes_final) - 1)
				mes_final = 13 - lm
				ano_final = rec.presupuesto_id.ano_final - (lapso_anos + 1)
			else:
				mes_final = int(rec.presupuesto_id.mes_final) - lapso_meses
				ano_final = int(rec.presupuesto_id.ano_final) - lapso_anos
			fecha_temporal = datetime(ano_final, mes_final, 1)
			fecha_final = fecha_temporal + \
				dateutil.relativedelta.relativedelta(months=1) + dateutil.relativedelta.relativedelta(days=-1)
			# Traer la ubicación del almacén General
			ubicacion = self.env['stock.location'].search([('complete_name', '=', 'SMM-G/Existencias')], limit=1)
			# Traer los datos de la partida para regresar el consumo
			filtro = [
				('date', '>=', fecha_inicial),
				('date', '<=', fecha_final),
				('product_category_name', '=', rec.presupuesto_id.categoria.complete_name),
				('product_id', '=', rec.product_id.id),
				('state', '=', 'done'),
				('location_id', '=', ubicacion.id),
				('location_dest_id', '=', rec.presupuesto_id.ubicacion_id.id)
			]
			cantidad = 0
			partidas = self.env['stock.move.line'].search(filtro)
			for p in partidas:
				cantidad += p.qty_done
			rec.cantidad_consumida_periodo_anterior = cantidad
			
	@api.model
	def _traer_cantidad_consumida_ano_anterior(self):
		# Calcular la fecha incial del año anterior
		for rec in self:
			# Calcular la fecha inicial y final de un año antes
			fecha_inicial = datetime(rec.presupuesto_id.ano_inicial-1, int(rec.presupuesto_id.mes_inicial), 1)
			fecha_temporal = datetime(rec.presupuesto_id.ano_final-1, int(rec.presupuesto_id.mes_final), 1)
			fecha_final = fecha_temporal + \
				dateutil.relativedelta.relativedelta(months=1) + dateutil.relativedelta.relativedelta(days=-1)
			# Traer la ubicación del almacén General
			ubicacion = self.env['stock.location'].search([('complete_name', '=', 'SMM-G/Existencias')], limit=1)
			# Traer los datos de la partida para regresar el consumo
			filtro = [
				('date', '>=', fecha_inicial),
				('date', '<=', fecha_final),
				('product_category_name', '=', rec.presupuesto_id.categoria.complete_name),
				('product_id', '=', rec.product_id.id),
				('state', '=', 'done'),
				('location_id', '=', ubicacion.id),
				('location_dest_id', '=', rec.presupuesto_id.ubicacion_id.id)
			]
			cantidad = 0
			partidas = self.env['stock.move.line'].search(filtro)
			for p in partidas:
				cantidad += p.qty_done
			rec.cantidad_consumida_ano_anterior = cantidad
