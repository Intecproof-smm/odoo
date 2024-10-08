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
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ExtendResPartner(models.Model):
    _inherit = 'res.partner'

    # ----------------------------------------------------------
    # Modificaciones al modelo / funciones
    # ----------------------------------------------------------
    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id, view_type, **options)
        self.x_eventos_abiertos = self.verificar_eventos_abiertos()
        return res

    # ----------------------------------------------------------
    # Base de datos
    # ----------------------------------------------------------
    x_paciente_medico = fields.Selection([
        ('Medico', 'Medico'),
        ('Paciente', 'Paciente'),
        ('Enfermera(o)', 'Enfermera(o)'),
        ('Paramédica(o)', 'Paramédica(o)'),
        ('Otro', 'Otro')
    ], string='Categoría', default='Paciente', tracking=True)
    x_medico_cedula = fields.Char(string='Cédula', tracking=True)
    x_medico_universidad = fields.Char(string='Universidad', tracking=True)
    x_medico_adscrito_residente = fields.Selection([
        ('Adscrito', 'Adscrito'), ('Residente', 'Residente')
    ], string='Tipo Médico', default='Adscrito', tracking=True)
    x_contacto_sexo = fields.Selection([
        ('Masculino', 'Masculino'), ('Femenino', 'Femenino')
    ], default='Masculino', tracking=True)
    
    # Esta relación se utiliza para los eventos, que son los casos en los que el paciente ingresa a la unidad médica
    x_eventos_medicos_ids = fields.One2many(
        comodel_name='smm_eventos_medicos',
        inverse_name='paciente_id',
        auto_join=True,
        string='Eventos Médicos',
        tracking=True
    )
    x_fecha_nacimiento = fields.Date(string='Fecha de nacimiento', tracking=True)
    x_edad_cumplida = fields.Char(string='Edad', compute='_calcular_edad', readonly=True)
    
    # Campos de SIREXE
    curp = fields.Char(string='CURP', tracking=True)
    url_expediente = fields.Char(string='URL del expediente médico', tracking=True)
    matricula_expediente = fields.Char(string='Matricula del expediente', tracking=True)
    link_expediente = fields.Char('Link expediente', compute='_compute_link_expediente')

    @api.depends('url_expediente', 'matricula_expediente')
    def _compute_link_expediente(self):
        for record in self:
            record.link_expediente = f'<a href="{record.url_expediente}" target="_blank">{record.matricula_expediente}</a>'

    # Verificar si tiene un evento abierto
    x_eventos_abiertos = fields.Integer(compute='_compute_eventos_abiertos')
    
    # ----------------------------------------------------------
    # Funciones e iniciación y cálculo de valores
    # ----------------------------------------------------------
    @api.onchange('x_fecha_nacimiento')
    def _calcular_edad(self):
        self.x_edad_cumplida = 'N/A'
        for contacto in self:
            if contacto.x_fecha_nacimiento:
                hoy = fields.date.today()
                contacto.x_edad_cumplida = str(int((hoy - contacto.x_fecha_nacimiento).days / 365))

    @api.depends('x_eventos_medicos_ids', 'x_eventos_abiertos', 'x_eventos_medicos_ids.estatus')
    def _compute_eventos_abiertos(self):
        eventos_abiertos = self.env['smm_eventos_medicos'].search([
                ('paciente_id', '=', self.id),
                ('estatus', '=', 'abierto')
        ])
        self.x_eventos_abiertos = len(eventos_abiertos)

    @api.constrains('x_eventos_medicos_ids')
    def _check_eventos_medicos_ids(self):
        if self.x_eventos_abiertos > 1:
            raise ValidationError(_('Existe un evento abierto y no se puede tener más de un evento abierto, '
                                    'cierra el evento anterior para continuar'))
        
    def verificar_eventos_abiertos(self):
        id_contacto = self._context.get('id_contacto') or self.id
        eventos_abiertos = self.env['smm_eventos_medicos'].search([
                ('paciente_id', '=', id_contacto),
                ('estatus', '=', 'abierto')
        ])
        return len(eventos_abiertos)

    def actualiza_eventos_abiertos(self):
        id_contacto = self.id
        eventos_abiertos = self.env['smm_eventos_medicos'].search([
                ('paciente_id', '=', id_contacto),
                ('estatus', '=', 'abierto')
        ])
        self.x_eventos_abiertos = len(eventos_abiertos)

    def agrupar_similares(self):
        selected_ids = self.env.context.get('active_ids', [])
        _logger.info("********* Selected_ids : "+str(selected_ids))
        selected_records = self.env['res.partner'].browse(selected_ids)
        _logger.info("********* Selected_records : "+str(selected_records))
        # Traer el primer valor de la lista para que todas las pos_orders sean cambiadas a ese paciente
        id_contacto = selected_records[0].id
        _logger.info("********* id_contacto : " + str(id_contacto))
        for partner in selected_records:
            if partner.id != id_contacto:
                # Traer todas las órdenes de POS del paciente
                pos_orders = self.env['pos.order'].browse([('partner_id', '=', partner.id)])
                for pos_order in pos_orders:
                    _logger.info("************** pos_order : " + str(pos_order) + " id : " + str(pos_order.id))
                    pos_order.update({"partner_id": id_contacto})
                # Traer todos los movimientos en stock_move del paciente para actualizarlas
                stock_moves = self.env['stock.move'].browse([('partner_id', '=', partner.id)])
                for stock_move in stock_moves:
                    _logger.info("************** stock_move : " + str(stock_move) + " id : " + str(stock_move.id))
                    stock_move.update([{"partner_id": id_contacto}])
                # Traer todos los movimientos en Stock_picking del paciente para actualizarlos
                stock_picks = self.env['stock.picking'].browse([('partner_id', '=', partner.id)])
                for stock_pick in stock_picks:
                    _logger.info("************** stock_pick : " + str(stock_pick) + " id : " + str(stock_pick.id))
                    stock_pick.update({"partner_id": id_contacto})
            