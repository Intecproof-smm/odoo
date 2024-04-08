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
from odoo import models, fields, api
from dateutil import relativedelta
import dateutil
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

meses = [
	('1', 'Enero'),
	('2', 'Febrero'),
	('3', 'Marzo'),
	('4', 'Abril'),
	('5', 'Mayo'),
	('6', 'Junio'),
	('7', 'Julio'),
	('8', 'Agosto'),
	('9', 'Septiembre'),
	('10', 'Octubre'),
	('11', 'Noviembre'),
	('12', 'Diciembre'),
]


class Presupuestos(models.Model):
	_name = 'smm_presupuestos'
	_description = 'Presupuestos de compra y consumo de productos en unidades'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	
	# ----------------------------------------------------------
	# Base de datos
	# ----------------------------------------------------------
	name = fields.Char(
		string='Nombre del presupuesto',
		readonly=True,
		compute='_compute_nombre_presupuesto',
		tracking=True,
		store=True,
	)
	ubicacion_id = fields.Many2one(
		comodel_name='stock.location',
		string='Ubicación',
		required=True,
		default=False,
		tracking=True,
		domain="[('name', '=', 'Existencias')]"
	)
	ubicacion_complete_name = fields.Char(related='ubicacion_id.complete_name', readonly=True, store=True)
	categoria = fields.Many2one(
		comodel_name='product.category',
		string="Categoría",
		tracking=True,
		required=True
	)
	mes_inicial = fields.Selection(
		meses,
		required=True,
		default=str(fields.date.today().month),
		tracking=True,
		string="Mes"
	)
	ano_inicial = fields.Integer(
		required=True,
		default=fields.date.today().year,
		tracking=True,
		string="Año"
	)
	fecha_inicial = fields.Date(string="Fecha inicial", readonly=True, store=True, compute='_compute_fecha_inicial')
	mes_final = fields.Selection(
		meses,
		required=True,
		default=str(fields.date.today().month),
		tracking=True,
		string="Mes"
	)
	ano_final = fields.Integer(
		required=True,
		default=fields.date.today().year,
		tracking=True,
		string="Año"
	)
	fecha_final = fields.Date(string="Fecha final", readonly=True, compute='_compute_fecha_final', store=True)
	presupuesto_line_ids = fields.One2many('smm_presupuestos_line', 'presupuesto_id', 'detalle', auto_join=True)
	
	@api.depends('ubicacion_id', 'categoria', 'fecha_inicial', 'fecha_final')
	def _compute_nombre_presupuesto(self):
		self.name = 'Sin datos completos'
		if self.ubicacion_complete_name and self.categoria:
			self.name = "%s - %s, %s - %s" % (
				self.ubicacion_complete_name or '', self.categoria.name or '',
				self.fecha_inicial, self.fecha_final
			)
	
	@api.depends('mes_inicial', 'ano_inicial')
	def _compute_fecha_inicial(self):
		self.fecha_inicial = datetime.strptime("1/" + str(self.mes_inicial) + "/" + str(self.ano_inicial), "%d/%m/%Y")
	
	@api.depends('mes_final', 'ano_final')
	def _compute_fecha_final(self):
		fecha_temporal = datetime.strptime("1/" + str(self.mes_final) + "/" + str(self.ano_final), "%d/%m/%Y")
		self.fecha_final = \
			fecha_temporal + dateutil.relativedelta.relativedelta(months=1) + dateutil.relativedelta.relativedelta(days=-1)

