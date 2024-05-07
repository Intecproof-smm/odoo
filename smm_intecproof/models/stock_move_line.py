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
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class StockMoveLineExtended(models.Model):
	_inherit = 'stock.move.line'
	
	# ----------------------------------------------------------
	# Definiciones de funciones
	# ----------------------------------------------------------
	def generar_presupuesto(self):
		# Mandar llamar la función que creará el presupuesto con los datos de la consulta
		# _logger.info("*********** Dentro de generar_presupuesto")
		self.env['smm_consulta_presupuestos']._generar_presupuesto()

	# ----------------------------------------------------------
	# Base de datos
	# ----------------------------------------------------------
	x_price_unit = fields.Float(related='product_id.list_price', readonly=True, store=True, check_company=True)
	x_rubro = fields.Many2one(related='product_id.rubro', readonly=True, store=True, check_company=True)
	x_subtotal = fields.Float(compute='_calcular_subtotal', readonly=True, store=False)
	x_receta = fields.Char(related='picking_id.x_receta', readonly=True, store=True)
	x_indicacion = fields.Char(realted='picking_id.x_indicacion', readonly=True, store=True)
	x_medico = fields.Char(related='picking_id.x_medico', readonly=True, store=True)

	@api.onchange('qty_done', 'x_price_unit')
	def _calcular_subtotal(self):
		for rec in self:
			rec.x_subtotal = 0
			# Traer el servicio seleccionado para poder calcular el costo
			if rec.product_id and rec.x_price_unit and rec.qty_done:
				rec.x_subtotal = rec.x_price_unit * rec.qty_done
