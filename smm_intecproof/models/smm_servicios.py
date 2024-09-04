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
import logging

_logger = logging.getLogger(__name__)


# Modelo para los servicios/procedimientos del evento
class SMMServicios(models.Model):
	_name = 'smm_servicios'
	_description = 'Servicios o procedimientos del evento del paciente'

	# ----------------------------------------------------------
	# Base de datos
	# ----------------------------------------------------------
	evento_id = fields.Many2one(
		comodel_name='smm_eventos_medicos',
		auto_join=True,
		string='Evento',
		readonly=True
	)
	producto_id = fields.Many2one(
		comodel_name='product.template',
		auto_join=True,
		string='Servicio/procedimiento',
		domain=[('detailed_type', '=', 'service')],
		ondelete='restict',
		readonly=False
	)
	cantidad = fields.Float(
		'Cantidad', default=1.0,
		digits='Product Unit of Measure', required=True
	)
	fecha_servicio = fields.Date(default=fields.Date.context_today)
	total = fields.Float(string="Total", compute='_calcular_costo_servicio', readonly=True)
	area_solicitud = fields.Selection(
		selection=[
			('urg', 'Urgencias')
			, ('hp', 'Hospital')
			, ('cons', 'Consulta')
			, ('uci', 'UCI')
			, ('quir', 'Quirofano')
			, ('ph', 'Prehospitalario')
			, ('tyo', 'T y O')
			, ('ane', 'Anestesio')
		]
		, string='Área que solicita'
		, store=True
	)
	turno = fields.Selection(
		selection=[
			('m', 'M')
			, ('v', 'V')
			, ('n1', 'N1')
			, ('n2', 'N2')
			, ('ja', 'JA')
			, ('jf', 'JF')
		]
		, string='Turno'
		, store=True
	)
	rubro = fields.Many2one(related='producto_id.rubro', readonly=True, store=True)

	@api.onchange('cantidad', 'producto_id')
	def _calcular_costo_servicio(self):
		for rec in self:
			# Traer el servicio seleccionado para poder calcular el costo
			if rec.producto_id:
				prod = self.env['product.template'].search([('id', '=', rec.producto_id.id)])
				if prod:
					rec.total = prod.list_price * rec.cantidad
				else:
					rec.total = 0
