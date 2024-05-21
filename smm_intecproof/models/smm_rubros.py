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


class Rubros(models.Model):
	_name = 'smm_rubros'
	_description = 'Rubros de medicamentos según Ley de ingresos del municipio de GDL'

	# ----------------------------------------------------------
	# Base de datos
	# ----------------------------------------------------------
	name = fields.Char(required=True, store=True, string='Rubro')
	descripcion = fields.Char(string = 'Descripción')
	categoria = fields.Char(string = 'Categoría')
	precio = fields.Float(string = 'Precio', digits='Product Price')