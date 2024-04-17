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

from odoo import api, models, fields
import logging

_logger = logging.getLogger(__name__)


class ConsumosPaciente(models.AbstractModel):
    _name = 'smm_report_consumos_paciente'
    _description = 'Reporte de consumos del paciente en un evento'
    
    @api.model
    def _get_report_values(self):
        # ctx = dict(self.env.context or {})
        lineas = self.env['stock.move.line'].browse(self.env.context.get('stock_move_line_ids'))
        for linea in lineas:
            stock_move_line = self.env['stock.move.line'].search([('id', 'in', linea.id)])
            nueva_linea = {
                'ubicacion': stock_move_line.location_id.name,
                'referencia': stock_move_line.reference,
                'fecha': stock_move_line.date,
                'turno': 'Turno',
                'area': 'Area',
                'producto': stock_move_line.product_id.name,
                'rubro': stock_move_line.x_rubro.name,
                'cantidad': stock_move_line.qty_done,
                'precio_unitario': stock_move_line.x_price_unit,
                'total': stock_move_line.x_subtotal
            }
            ml = super(ConsumosPaciente, self).create(nueva_linea)
            # ml = self.env['smm_report_consumos_paciente'].create(nueva_linea)
            # self.env['smm_report_consumos_paciente'].create(nueva_linea)
        data = self.env['smm_report_consumos_paciente'].search()
        return {
            'doc_model': self.env['smm_report_consumos_paciente'],
            'data': data,
            'docs': self.env['smm_report_consumos_paciente'].browse(),
        }

    # ----------------------------------------------------------
    # Base de datos
    # ----------------------------------------------------------
    ubicacion = fields.Char()
    referencia = fields.Char()
    fecha = fields.Date()
    turno = fields.Char()
    area = fields.Char()
    producto = fields.Char()
    rubro = fields.Char()
    cantidad = fields.Float()
    precio_unitario = fields.Float()
    total = fields.Float()
    