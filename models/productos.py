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
from odoo import models, fields


class ExtendProducts(models.Model):
	_inherit = 'product.template'

	# ----------------------------------------------------------
	# Base de datos
	# ----------------------------------------------------------

	def _branch_id_domain(self):
		"""Creamos el filtro para las ubicaciones por el branch del usuario."""
		# ('branch_id', '=', self.env['res.users'].search([('id', '=', self.env.user.id)]).branch_id.id)
		# ('branch_id', '=', self.env.user.branch_id.id)
		return [('branch_id', '=', self.env.user.branch_id.id)]
	ubicacion_ids = fields.Many2many('res.ubicaciones', string='Ubicaciones', default=False, domain=_branch_id_domain)

