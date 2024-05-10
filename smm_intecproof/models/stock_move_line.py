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
	@api.model
	def _calcular_branches_permitidos(self):
		for rec in self:
			rec.x_branches = self.env.user.branch_ids.ids

	def generar_presupuesto(self):
		# Mandar llamar la función que creará el presupuesto con los datos de la consulta
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
	x_branches = fields.Many2many('res.branch', compute='_calcular_branches_permitidos', readonly=True, store=False)

	@api.onchange('qty_done', 'x_price_unit')
	def _calcular_subtotal(self):
		for rec in self:
			rec.x_subtotal = 0
			# Traer el servicio seleccionado para poder calcular el costo
			if rec.product_id and rec.x_price_unit and rec.qty_done:
				rec.x_subtotal = rec.x_price_unit * rec.qty_done

	@api.model
	def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **read_kwargs):
		context = self._context
		if 'ignorar_regla_branches' in context and context['ignorar_regla_branches']:
			res = super(StockMoveLineExtended, self.sudo()).search_read(domain, fields, offset, limit, order)
		else:
			res = super(StockMoveLineExtended, self).search_read(domain, fields, offset, limit, order)
		return res

	def llamar_lista_controlados(self):
		branches = self.env.user.branch_ids.ids
		_logger.info("*********** Branches permitidos : " + str(branches))
		ubicaciones = self.env['stock.location'].search([('x_branch', 'in', branches)])
		# dominio = [
		# 	"&", ("state", "=", "done"), "&", ("product_id.is_controlled_product", "=", True), "&", "|",
		# 	("picking_id.picking_type_id.code", "=", "internal"), "|", ("picking_id.picking_type_id.code", "=", "incoming"),
		# 	("picking_id.picking_type_id.code", "=", "outgoing"), "|", ("location_id", "in", ubicaciones.ids),
		# 	("location_dest_id", "in", ubicaciones.ids)]
		dominio = [
			"&", ("state", "=", "done"), "&", ("product_id.is_controlled_product", "=", True), "|",
			("location_id", "in", ubicaciones.ids), ("location_dest_id", "in", ubicaciones.ids)
		]
		_logger.info("*********** El dominio para controlados es: " + str(dominio))
		return {
			'type': 'ir.actions.act_window',
			'name': ' Reporte de controlados 2',
			'view_type': 'tree',
			'view_mode': 'tree',
			'res_model': 'stock.move.line',
			'domain': dominio,
			'target': 'current',
			'context': {
				'tree_view_ref': 'smm_intecproof.movimientos_de_controlados_tree',
				'group_by': 'product_id',
				'ignorar_regla_branches': True,
			},
		}
