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


class Ubicaciones(models.Model):
	_name = 'res.ubicaciones'
	_description = 'Ubicaciones físicas de los productos por Branch'

	# ----------------------------------------------------------
	# Definiciones de inicialización o valores
	# ----------------------------------------------------------

	@api.model
	def default_get(self, default_fields):
		# Inicializar los campos según los valores del producto y branch
		res = super(Ubicaciones, self).default_get(default_fields)
		valor = self.env['res.users'].sudo().search([('id', '=', self.env.user.id)]).branch_id.id
		res['branch_id'] = valor
		# self.env['res.users'].sudo().search([('id', '=', self.env.user.id)]).branch_id
		res['product_id'] = self.env.context.get('product_id')
		return res

	# ----------------------------------------------------------
	# Base de datos
	# ----------------------------------------------------------
	name = fields.Char(required=True, store=True, string='Ubicación')
	product_id = fields.Many2one('product.template', required=True, string='Producto')
	branch_id = fields.Many2one('res.branch', required=True, string='Branch')
