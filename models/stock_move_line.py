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
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)


class StockMoveLineExtended(models.Model):
	_inherit = 'stock.move.line'
	
	# ----------------------------------------------------------
	# Definiciones de funciones
	# ----------------------------------------------------------
	
	def generar_presupuesto(self):
		# Mandar llamar la función que creará el presupuesto con los datos de la consulta
		_logger.info("*********** Dentro de generar_presupuesto")
		self.env['smm_consulta_presupuestos']._generar_presupuesto()
