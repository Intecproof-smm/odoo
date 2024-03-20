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
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


# Modelo para el evento médico
class SMMEventosMedicos(models.Model):
    _name = 'smm_eventos_medicos'
    _description = 'Eventos médicos del paciente'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def default_get(self, fields):
        eventos_abiertos = self._context.get('eventos_abiertos')
        _logger.info("********* eventos_abiertos : "+str(eventos_abiertos))
        if eventos_abiertos > 0:
            raise ValidationError(_('Existe un evento abierto y no se puede tener más de un evento abierto, cierra el evento anterior para continuar'))
        else:
            res = super(SMMEventosMedicos, self).default_get(fields)
        return res
    
    # ----------------------------------------------------------
    # Base de datos
    # ----------------------------------------------------------
    paciente_id = fields.Many2one(
        comodel_name='res.partner',
        auto_join=True,
        string='Paciente',
        readonly=True
    )
    evento_medico = fields.Char(
        string='Número de evento', index=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('evento_medico'),
        required=True, copy=False, readonly=True
    )
    fecha_inicio = fields.Date(string='Fecha de ingreso', default=datetime.today(), tracking=True, readonly=True)
    fecha_termino = fields.Date(string='Fecha de la alta', tracking=True, readonly=True)
    estatus = fields.Selection(
        [
            ('abierto', 'Abierto'),
            ('cerrado', 'Cerrado')
        ],
        string='Estado',
        default='abierto',
    )
    servicios_ids = fields.One2many('smm_servicios', 'evento_id', 'Servicios', readonly=True)
    estudio_socioeconomico = fields.Boolean('Se realizó estudio socioeconómico', tracking=True)
    
    # Motivos de la alta
    mot_alta_1 = fields.Char(string='Motivo de alta 1')
    mot_alta_2 = fields.Char(string='Motivo de alta 2')
    mot_alta_3 = fields.Char(string='Motivo de alta 3')
    fam_responsable = fields.Many2one(
        comodel_name='res.partner',
        auto_join=True,
        tracking=True,
        string='Familiar Responsable'
    )
    fam_responsable_tel = fields.Char(string='Teléfono del familiar responsable')
    
    # Exploración
    explora_peso = fields.Integer(string='Peso (kgm)')
    explora_talla = fields.Integer(string='Talla (mts)')
    explora_ta = fields.Char(string='TA (mmHg)')
    explora_fc_pulso = fields.Integer(string='FC/Pulso (x min)')
    explora_fr = fields.Char(string='FR (x min)')
    explora_temp = fields.Integer(string='°C')
    explora_habitus = fields.Char(string='Habitus exterior')
    explora_piel_anexos = fields.Char(string='Piel y anexos')
    explora_cabeza_cuello = fields.Char(string='Cabeza y cuello')
    explora_torax = fields.Char(string='Tórax')
    explora_abdomen = fields.Char(string='Abdomen')
    explora_genitales = fields.Char(string='Genitales')
    explora_extremidades = fields.Char(string='Extremidades')
    explora_sis_nervioso = fields.Char(string='Sistema nervioso')
    explora_examen_previo = fields.Text(string='Exámenes de laboratorio previos')
    
    # Integración diagnostica
    integra_diag_1 = fields.Char(string='Diagnostico 1')
    integra_diag_2 = fields.Char(string='Diagnostico 2')
    integra_diag_3 = fields.Char(string='Diagnostico 3')
    integra_diag_4 = fields.Char(string='Diagnostico 4')
    integra_plan_estudio_1 = fields.Char(string='Plan de estudio 1')
    integra_plan_estudio_2 = fields.Char(string='Plan de estudio 2')
    integra_plan_estudio_3 = fields.Char(string='Plan de estudio 3')
    integra_plan_estudio_4 = fields.Char(string='Plan de estudio 4')
    integra_plan_manejo_1 = fields.Char(string='Plan de manejo 1')
    integra_plan_manejo_2 = fields.Char(string='Plan de manejo 2')
    integra_plan_manejo_3 = fields.Char(string='Plan de manejo 3')
    integra_plan_manejo_4 = fields.Char(string='Plan de manejo 4')
    integra_pronostico = fields.Text(string='Pronóstico')
    integra_nombre_elaboro_historia = fields.Char(string='Nombre del médico que elaboró la historia')
    integra_nombre_avala_historia = fields.Char(string='Nombre del médico que avala la historia')

    # Observaciones / comentarios finales
    observa_observa_comenta = fields.Text(string='Observaciones/Comentarios finales')
    
    @api.onchange('estatus', 'fecha_termino')
    def _calcula_fecha_cierre(self):
        if self.estatus == 'cerrado':
            self.fecha_termino = fields.Date.today()
        else:
            self.fecha_termino = None

        res = self.env['res.partner'].actualiza_eventos_abiertos
        
   

