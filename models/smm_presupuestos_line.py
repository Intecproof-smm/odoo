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
