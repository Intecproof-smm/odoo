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
	
	# ----------------------------------------------------------
	# Definiciones de funciones
	# ----------------------------------------------------------
	@api.model
	def _generar_presupuesto(self):
		# Traer el contexto para obtener los valores de los datos
		ctx = dict(self.env.context or {})
		ubicacion = ctx['location_dest_id']
		categoria = ctx['categoria_id']
		fecha_inicial = datetime.strptime(ctx['fecha_inicial'], "%Y-%m-%d")
		mes_inicial = fecha_inicial.month
		ano_inicial = fecha_inicial.year
		fecha_final = datetime.strptime(ctx['fecha_final'], "%Y-%m-%d")
		mes_final = fecha_final.month
		ano_final = fecha_final.year
		# Crear el filtro para traer las partidas
		filtro = [
			('date', '>=', fecha_inicial),
			('date', '<=', fecha_final),
			('product_category_name', '=', ctx['nombre_categoria']),
			('state', '=', 'done'),
			('location_id', '=', ctx['location_id']),
			('location_dest_id', '=', ubicacion)
		]
		campos = ['product_id', 'date', 'qty_done:sum', 'product_id.id']
		agrupador = ['product_id']
		orden = 'product_id'
		# Crear el registro de Presupuestos
		nuevo_presupuesto = self.env['smm_presupuestos'].create({
			'name': "Se calculará automáticamente",
			'ubicacion_id': ubicacion,
			'categoria': categoria,
			'mes_inicial': str(mes_inicial),
			'ano_inicial': str(ano_inicial),
			'mes_final': str(mes_final),
			'ano_final': str(ano_final),
		})
		# Traer las lineas de Stock_move que pasen el filtro
		partidas = self.env['stock.move.line'].read_group(
			domain=filtro, fields=campos, groupby=agrupador, orderby=orden, offset=0, limit=None, lazy=False
		)
		# Crear cada una de las partidas que pasaron el filtro
		for p in partidas:
			self.env['smm_presupuestos_line'].create({
				'presupuesto_id': nuevo_presupuesto.id,
				'product_id': str(p['product_id'][0]),
				'cantidad': p['qty_done'],
			})

	# ----------------------------------------------------------
	# Campos de la base de datos
	# ----------------------------------------------------------
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
		_logger.info("************* Valores de mes_inicial %s y año_inicial %s", str(self.mes_inicial), str(self.ano_inicial))
		if self.mes_inicial and self.ano_inicial:
			for rec in self:
				rec.fecha_inicial = datetime.strptime("1/" + str(rec.mes_inicial) + "/" + str(rec.ano_inicial), "%d/%m/%Y")
	
	@api.depends('mes_final', 'ano_final')
	def _compute_fecha_final(self):
		fecha_temporal = datetime.strptime("1/" + str(self.mes_final) + "/" + str(self.ano_final), "%d/%m/%Y")
		self.fecha_final = \
			fecha_temporal + dateutil.relativedelta.relativedelta(months=1) + dateutil.relativedelta.relativedelta(
				days=-1)
	
	def traer_datos_consulta(self):
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
		ctx['fecha_inicial'] = self.fecha_inicial
		ctx['fecha_final'] = self.fecha_final
		ctx['consulta_presupuesto'] = True
		ctx['categoria_id'] = self.categoria.id
		ctx['nombre_categoria'] = self.categoria.complete_name
		ctx['location_dest_id'] = self.ubicacion_id.id
		ctx['location_id'] = ubicacion.id

		_logger.info("********** Contenido del contexto : " + str(ctx))
		# Obtener el identificador de la vista de lista que necesito para mostrar el resultado
		tree_view_id = self.env.ref('smm_intecproof.view_move_line_tree_presupuestos').id
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
	
	def _traer_cantidades_consumidas(self, product_id):
		ubicacion = self.env['stock.location'].search([('complete_name', '=', 'SMM-G/Existencias')], limit=1)
		filtro = [
			('date', '>=', self.fecha_inicial),
			('date', '<=', self.fecha_final),
			('product_category_name', '=', self.categoria.complete_name),
			('product_id', '=', product_id),
			('state', '=', 'done'),
			('location_id', '=', ubicacion.id),
			('location_dest_id', '=', self.ubicacion_id.id)
		]
		campos = ['product_id', 'date', 'qty_done:sum', 'product_id.id']
		agrupador = ['product_id']
		orden = 'product_id'
		partidas = self.env['stock.move.line'].read_group(
			domain=filtro, fields=campos, groupby=agrupador, orderby=orden, offset=0, limit=None, lazy=False
		)
		# Traer los datos de la partida para regresar el consumo
		for p in partidas:
			return p['qty_done']
