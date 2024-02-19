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
from dateutil.relativedelta import relativedelta
from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class ExtendStock_lot(models.Model):
	_inherit = 'stock.lot'

	# ----------------------------------------------------------
	# Definiciones de funciones
	# ----------------------------------------------------------

	@api.model
	def get_medicamentos_data(self):
		id_location = self.traer_location_data()
		total_medicamentos_vencidos = self.env['stock.lot'].search([
			('product_id.categ_id.name', '=', 'Medicamentos'),
			('quant_ids.quantity', '>', '0'),
			('expiration_date', '<', fields.date.today()),
			('quant_ids.location_id', '=', id_location)
		])
		total_medicamentos_hoy_vencen = self.env['stock.lot'].search([
			('product_id.categ_id.name', '=', 'Medicamentos'),
			('quant_ids.quantity', '>', '0'),
			('expiration_date', '>=', fields.date.today().strftime('%Y-%m-%d 00:00:00')),
			('expiration_date', '<=', fields.date.today().strftime('%Y-%m-%d 23:59:59')),
			('quant_ids.location_id', '=', id_location)
		])
		total_medicamentos_proximos_a_vencer = self.env['stock.lot'].search([
			('product_id.categ_id.name', '=', 'Medicamentos'),
			('quant_ids.quantity', '>', '0'),
			('expiration_date', '>=', fields.date.today()+relativedelta(days=1)),
			('expiration_date', '<=', fields.date.today()+relativedelta(months=1)),
			('quant_ids.location_id', '=', id_location)
		])
		total_medicamentos_ok = self.env['stock.lot'].search([
			('product_id.categ_id.name', '=', 'Medicamentos'),
			('quant_ids.quantity', '>', '0'),
			('expiration_date', '>', fields.date.today()+relativedelta(months=1)),
			('quant_ids.location_id', '=', id_location)
		])
		return {
			'total_medicamentos_vencidos': len(total_medicamentos_vencidos),
			'total_medicamentos_hoy_vencen': len(total_medicamentos_hoy_vencen),
			'total_medicamentos_proximos_a_vencer': len(total_medicamentos_proximos_a_vencer),
			'total_medicamentos_ok': len(total_medicamentos_ok)
		}

	@api.model
	def traer_location_data(self):
		location = self.env['stock.location'].search([('x_branch', '=', self.env.user.branch_id.id)])
		_logger.info("El resultado de location.id es : " + str(location.id))
		return location.id
	