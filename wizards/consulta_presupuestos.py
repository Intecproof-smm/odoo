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
from odoo import models, fields, api, _
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


class ConsultaPresupuestos(models.TransientModel):
	_name = 'smm_consulta_presupuestos'
	_description = 'Consulta presupuestos Wizard'
	
	ubicacion_id = fields.Many2one(
		comodel_name='stock.location',
		string='Ubicación',
		required=True,
		default=False,
		tracking=True,
		domain="[('name', '=', 'Existencias')]"
	)
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
	
	consulta_line_ids = fields.Many2one(
		comodel_name='stock.move.line',
		string='Detalle'
	)
	
	@api.depends('mes_inicial', 'ano_inicial')
	def _compute_fecha_inicial(self):
		self.fecha_inicial = datetime.strptime("1/" + str(self.mes_inicial) + "/" + str(self.ano_inicial), "%d/%m/%Y")
	
	@api.depends('mes_final', 'ano_final')
	def _compute_fecha_final(self):
		fecha_temporal = datetime.strptime("1/" + str(self.mes_final) + "/" + str(self.ano_final), "%d/%m/%Y")
		self.fecha_final = \
			fecha_temporal + dateutil.relativedelta.relativedelta(months=1) + dateutil.relativedelta.relativedelta(
				days=-1)
	
	def traer_datos_consulta(self):
		_logger.info("******** Entré a traer_datos_consulta ********")
		# Obtener el id de la ubicación SMM-G/Existencias
		ubicacion = self.env['stock.location'].search([('complete_name', '=', 'SMM-G/Existencias')], limit=1)
		# Cambiar las fechas de Date a Datetime para poder hacer el filtro de manera completa
		fecha_ini = datetime(self.fecha_inicial.year, self.fecha_inicial.month, self.fecha_inicial.day)
		fecha_fin = datetime(self.fecha_final.year, self.fecha_final.month, self.fecha_final.day)
		filtro = [
			('date', '>=', fecha_ini),
			('date', '<=', fecha_fin),
			('product_category_name', '=', self.categoria.complete_name),
			('state', '=', 'done'),
			('location_id', '=', ubicacion.id),
			('location_dest_id', '=', self.ubicacion_id.id)
		]
		# Traer el contexto para actualizar los agrupadores
		ctx = dict(self.env.context or {})
		ctx['inventory_report_mode'] = True
		ctx['group_by'] = ['product_id', 'date:month']
		# Obtener el identificador de la vista de lista que necesito para mostrar el resultado
		tree_view_id = self.env.ref('stock.view_move_line_tree').id
		# Mandar llamar la list del modelo stock_move_line ya existente
		return {
			'type': 'ir.actions.act_window',
			'views': [(tree_view_id, 'tree')],
			'view_mode': 'tree',
			'context': ctx,
			'name': _(
				'Consulta de ' + self.categoria.name + ' en ' + self.ubicacion_id.complete_name + ' del ' +
				str(self.fecha_inicial) + ' al ' + str(self.fecha_final)),
			'res_model': 'stock.move.line',
			'domain': filtro,
		}
	