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
from odoo import models, fields
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
		readonly=False
	)
	cantidad = fields.Float(
		'Cantidad', default=1.0,
		digits='Product Unit of Measure', required=True
	)
	fecha_servicio = fields.Date(default=fields.Date.context_today)
	

