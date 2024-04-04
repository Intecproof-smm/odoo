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
        res = super(SMMEventosMedicos, self).default_get(fields)
        eventos_abiertos = self._context.get('eventos_abiertos') or 0
        if eventos_abiertos > 0:
            raise ValidationError(_('Existe un evento abierto y no se puede tener más de un evento abierto, cierra el evento anterior para continuar'))
        return res
    
    def write(self, vals):
        # Validar que no exista más de un evento abierto si se está cambiando el estatus
        if vals.get('estatus') == 'abierto' and self.estatus == 'cerrado':
            # Actualizar el context de manera manual
            eventos_abiertos = self.env.context.get('eventos_abiertos')
            if eventos_abiertos:
                if eventos_abiertos > 0:
                    vals['estatus'] = self.estatus
                    super(SMMEventosMedicos, self).write({'estatus': self.estatus})
                    raise ValidationError(_('No se puede tener más de un evento abierto de manera simultánea'))
        # Verificar si se cambió el estatus, entonces poblar la fecha de cierre
        if vals.get('estatus'):
            if vals['estatus'] == 'cerrado':
                vals['fecha_termino'] = fields.date.today()
            else:
                vals['fecha_termino'] = None
        res = super(SMMEventosMedicos, self).write(vals)
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
    pos_order_line_ids = fields.One2many(
        comodel_name='pos.order.line',
        string='Ordenes',
        compute='_traer_datos_pos_order'
    )
    evento_medico = fields.Char(
        string='Número de evento', index=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('evento_medico'),
        required=True, copy=False, readonly=True
    )
    fecha_inicio = fields.Date(string='Fecha de ingreso', default=datetime.today(), tracking=True)
    fecha_termino = fields.Date(string='Fecha de salida/alta', tracking=True)
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
    
    # Resultados del estudio socioeconómico
    res_se_folio = fields.Char(string="Folio")
    res_se_fecha = fields.Char(string="Fecha", default=fields.date.today())
    res_se_observaciones = fields.Text(string="Observaciones")
    res_se_ocupacion = fields.Float(string="Ocupación")
    res_se_vivienda = fields.Float(string="Vivienda")
    res_se_salud_familiar = fields.Float(string="Salud familiar")
    res_se_ingreso_familiar = fields.Float(string="Ingreso familiar")
    res_se_egreso_familiar = fields.Float(string="Egreso familiar")
    res_se_sumatoria_resultado = fields.Float(
        string="Sumatoria",
        readonly=True,
        store=False,
        compute='_calcular_resultado'
    )

    @api.onchange(
        'res_se_ocupacion', 'res_se_vivienda', 'res_se_salud_familiar',
        'res_se_ingreso_familiar', 'res_se_egreso_familiar'
    )
    def _calcular_resultado(self):
        for res in self:
            res.res_se_sumatoria_resultado = \
                res.res_se_ocupacion + res.res_se_vivienda + res.res_se_salud_familiar + res.res_se_ingreso_familiar \
                + res.res_se_egreso_familiar

    @api.onchange('estatus')
    def _calcula_fecha_cierre(self):
        if self.estatus == 'Cerrado':
            self.fecha_termino = fields.Date.today()
        else:
            self.fecha_termino = None
        
    def _traer_datos_pos_order(self):
        for rec in self:
            fecha_inicial = rec.fecha_inicio
            if rec.fecha_termino:
                fecha_final = rec.fecha_termino
            else:
                fecha_final = fields.date.today()
            # Traer los datos de lad órdenes del punto de venta que estén asignadas al paciente y dentro de las fechas
            pos_ordenes = self.env['pos.order'].search(
                [
                    ('id', 'in', rec.paciente_id.pos_order_ids.ids),
                    ('date_order', '>=', fecha_inicial),
                    ('date_order', '<=', fecha_final)
                ]
            )
            # Traer los datos de las líneas de las órdenes del punto de venta que estén dentro de las fechas
            rec.pos_order_line_ids = self.env['pos.order.line'].search(
                [
                    ('order_id', 'in', pos_ordenes.ids)
                ]
            )

    def action_cerrar_evento(self):
        self.estatus = 'cerrado'
        
    def action_abrir_evento(self):
        self.estatus = 'abierto'
    