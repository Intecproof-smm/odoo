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
from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

# Añade los campos para la selección de la categoría


class ExtendResPartner(models.Model):
    _inherit = 'res.partner'

    # ----------------------------------------------------------
    # Base de datos
    # ----------------------------------------------------------
    x_paciente_medico = fields.Selection([
        ('Medico', 'Medico'), ('Paciente', 'Paciente'), ('Otro', 'Otro')
    ], string='Categoría', defaul='Paciente', tracking=True)
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
    x_identificacion_oficial_tipo = fields.Selection([
        ('INE', 'INE'), ('Pasaporte', 'Pasaporte'), ('Licencia', 'Licencia'), ('Otro', 'Otro'),
        ('Sin Identificación', 'Sin Identificación'), ('Sin especificar', 'Sin especificar')
    ], string='Tipo de ID', default='Sin especificar', tracking=True)
    x_identificacion_oficial = fields.Char(string='Identificación', tracking=True)
    x_fecha_nacimiento = fields.Date(string='Fecha de nacimiento', tracking=True)
    x_edad_cumplida = fields.Char(string='Edad', computer='_calcular_edad', readonly=True)
    x_escolaridad = fields.Selection([
        ('Primaria', 'Primaria'), ('Secundaria', 'Secundaria'), ('Tecnólogo', 'Tecnólogo'),
        ('Bachillerato', 'Bachillerato'), ('Profesional técnico', 'Profesional técnico'),
        ('Técnico sup. Universitario ', 'Técnico sup. Universitario'), ('Licenciatura ', 'Licenciatura'),
        ('Especialización', 'Especialización'), ('Maestría', 'Maestría'), ('Doctorado', 'Doctorado'),
        ('Otro', 'Otro'), ('Sin especificar', 'Sin especificar')
    ], string='Escolaridad', default='Sin especificar', tracking=True)
    x_seguridad_social = fields.Selection([
        ('IMSS', 'IMSS'), ('ISSSTE', 'ISSSTE'), ('Seguro Popular', 'Seguro Popular'),
        ('Ninguno', 'Ninguno'), ('Otro', 'Otro'), ('Sin especificar', 'Sin especificar')
    ], string='Tipo de SS', default='Sin especificar', tracking=True)
    x_edo_civil = fields.Selection([
        ('Soltero', 'Soltero'), ('Casado', 'Casado'), ('Viudo', 'Viudo'), ('Concubinato', 'Concubinato'),
        ('Divorciado', 'Divorciado'), ('Separado', 'Separado'), ('Sin especificar', 'Sin especificar')
    ], string='Estado civil', default='Sin especificar', tracking=True)
    x_ocupacion = fields.Selection([
        ('Ama de casa', 'Ama de casa'), ('Estudiante', 'Estudiante'), ('Empleado', 'Empleado'),
        ('Servicios domésticos', 'Servicios domésticos'), ('Trabajador en un oficio', 'Trabajador en un oficio'),
        ('Comerciante', 'Comerciante'), ('Técnico', 'Técnico'), ('Profesionista', 'Profesionista'),
        ('Vendedor ambulante', 'Vendedor ambulante'), ('Desempleado', 'Desempleado'), ('Otro', 'Otro'),
        ('Sin especificar', 'Sin especificar')
    ], string='Ocupación', default='Sin especificar', tracking=True)
    x_religion = fields.Selection([
        ('Católica', 'Católica'), ('Protestante', 'Protestante'), ('Cristiana', 'Cristiana'),
        ('Testigos de Jehová', 'Testigos de Jehová'), ('Pentecostales', 'Pentecostales'), ('Evangélica', 'Evangélica'),
        ('Ateo', 'Ateo'), ('Otra', 'Otra'), ('Sin especificar', 'Sin especificar')
    ], string='Religión', default='Sin especificar', tracking=True)
    x_nombre_madre = fields.Char(string='Nombre de la madre', tracking=True)
    x_nombre_padre = fields.Char(string='Nombre del padre', tracking=True)
    x_capacidad_distinta = fields.Selection([
        ('Sin capacidad distinta', 'Sin capacidad distinta'), ('Física', 'Física'), ('Auditiva', 'Auditiva'),
        ('Visual', 'Visual'), ('Sordoceguera', 'Sordoceguera'), ('Intelectual', 'Intelectual'),
        ('Psicosocial', 'Psicosocial'), ('Múltiple', 'Múltiple'), ('Sin especificar', 'Sin especificar')
    ], string='Capacidad distinta', default='Sin especificar', tracking=True)
    x_tipo_sangre = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'),
        ('O-', 'O-'), ('Sin especificar', 'Sin especificar')
    ], string='Tipo Sanguíneo', default='Sin especificar', tracking=True)
    x_fam_responsable = fields.Many2one(
        comodel_name='res.partner',
        auto_join=True,
        tracking=True,
        string='Familiar Responsable'
    )

    # antececentes heredados de familiares
    # --- To do ---
    # Se deberá de crear una tabla para los parientes con diabetes, cancer, cardiopatias, malformaciones, etc.
    # -------------
    x_her_diabetes = fields.Boolean('Diabetes', tracking=True)
    x_her_diabetes_quien = fields.Selection([
        ('Padre', 'Padre'), ('Madre', 'Madre'), ('Abuelos', 'Abuelos'), ('Hermanos', 'Hermanos'), ('Tios', 'Tios')
    ], string='¿Quién?', tracking=True)
    x_her_cancer = fields.Boolean('Cancer', tracking=True)
    x_her_cancer_quien = fields.Selection([
        ('Padre', 'Padre'), ('Madre', 'Madre'), ('Abuelos', 'Abuelos'), ('Hermanos', 'Hermanos'), ('Tios', 'Tios')
    ], string='¿Quién?', tracking=True)
    x_her_cancer_tipo = fields.Selection([
        ('Seno', 'Seno'), ('Colon', 'Colon'), ('Pulmón', 'Pulmón'), ('Próstata', 'Próstata'), ('Piel', 'Piel'),
        ('Otro', 'Otro'), ('Sin especificar', 'Sin especificar')
    ], string='Tipo de cancer', default='Sin especificar', tracking=True)
    x_her_cardiopatias = fields.Boolean('Cardiopatias', tracking=True)
    x_her_cardiopatias_quien = fields.Selection([
        ('Padre', 'Padre'), ('Madre', 'Madre'), ('Abuelos', 'Abuelos'), ('Hermanos', 'Hermanos'), ('Tios', 'Tios')
    ], string='¿Quién?', tracking=True)
    x_her_malformaciones = fields.Boolean('Malformaciones', tracking=True)
    x_her_malformaciones_quien = fields.Selection([
        ('Padre', 'Padre'), ('Madre', 'Madre'), ('Abuelos', 'Abuelos'), ('Hermanos', 'Hermanos'), ('Tios', 'Tios')
    ], string='¿Quién?', tracking=True)
    x_her_malformaciones_tipo = fields.Selection([
        ('Microcefalia', 'Microcefalia'), ('Catarata congénita', 'Catarata congénita'),
        ('Acondroplasia', 'Acondroplasia'), ('Hipertelorismo', 'Hipertelorismo'),
        ('Pie plano congénito', 'Pie plano congénito'), ('Otra', 'Otra'), ('Sin especificar', 'Sin especificar')
    ], string='Tipo', default='Sin especificar', tracking=True)
    x_her_hipertension = fields.Boolean('Hipertensión', tracking=True)
    x_her_hipertension_quien = fields.Selection([
        ('Padre', 'Padre'), ('Madre', 'Madre'), ('Abuelos', 'Abuelos'), ('Hermanos', 'Hermanos'), ('Tios', 'Tios')
    ], string='¿Quién?', tracking=True)
    x_her_nefropatas = fields.Boolean('Nefropatas', tracking=True)
    x_her_nefropatas_quien = fields.Selection([
        ('Padre', 'Padre'), ('Madre', 'Madre'), ('Abuelos', 'Abuelos'), ('Hermanos', 'Hermanos'), ('Tios', 'Tios')
    ], string='¿Quién?', tracking=True)
    x_her_otro = fields.Boolean('Otro', tracking=True)
    x_her_otro_cual = fields.Char(string='Especificar', tracking=True)
    # antececentes No patologicos
    x_nopat_tabaquismo = fields.Boolean('Tabaquismo', tracking=True)
    x_nopat_tabaquismo_cuantos_dia = fields.Integer(string='¿Cuántos por día?', tracking=True)
    x_nopat_tabaquismo_anos_consumo = fields.Integer(string='¿Años de consumo?', tracking=True)
    x_nopat_exfumador_o_pasivo = fields.Boolean('¿Exfumador o pasivo?', tracking=True)
    x_nopat_alcohol = fields.Boolean('Alcohol', tracking=True)
    x_nopat_alcohol_copas_semana = fields.Integer(string='¿Copas por semana?', tracking=True)
    x_nopat_alcohol_anos_consumo = fields.Integer(string='¿Años de consumo?', tracking=True)
    x_nopat_exalcoholico_u_ocacional = fields.Boolean('Exalcoholico u ocasional', tracking=True)
    x_nopat_alergias = fields.Boolean('Alergias', tracking=True)
    x_nopat_alergias_tipo = fields.Selection([
        ('A medicinas', 'A medicinas'), ('Estacional', 'Estacional'), ('De interior', 'De interior'),
        ('A mascotas', 'A mascotas'), ('Cutáneas', 'Cutáneas'), ('Al polen', 'Al polen'), ('Otra', 'Otra'),
        ('Sin especificar', 'Sin especificar')
    ], string='Tipo de alergia', default='Sin especificar', tracking=True)
    x_nopat_tipo_sangre_ = fields.Selection([
        ('Se desconoce', 'Se desconoce'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'),
        ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'), ('Sin especificar', 'Sin especificar')
    ], string='Tipo sanguíneo', default='Sin especificar', tracking=True)
    x_nopat_alimenta_adecuada = fields.Boolean('Alimentación adecuada', tracking=True)
    x_nopat_vivienda_servicios_basicos = fields.Boolean('Servicios básicos', tracking=True)
    x_nopat_droga = fields.Boolean('Drogadicción', tracking=True)
    x_nopat_droga_tipo = fields.Selection([
        ('Legales', 'Legales'), ('Ilegales', 'Ilegales'), ('Estimulantes', 'Estimulantes'),
        ('Depresoras', 'Depresoras'), ('Psicodélicas', 'Psicodélicas'), ('Otras', 'Otras'),
        ('Sin especificar', 'Sin especificar')
    ], string='Tipo', default='Sin especificar', tracking=True)
    x_nopat_droga_anos_consumo = fields.Integer(string='¿Años de consumo?', tracking=True)
    x_nopat_droga_ex = fields.Boolean('Exdrogadicto', tracking=True)
    x_nopat_otro = fields.Boolean('Otros', tracking=True)
    x_nopat_otro_desc = fields.Char('Descripción', tracking=True)
    # antecedentes parciales patológicos
    x_parc_enfer_infancia = fields.Char(string='Enfermedades de la infancia', tracking=True)
    x_parc_enfer_infancia_sec = fields.Char(string='¿Secuelas?', tracking=True)
    x_parc_hosp_previa = fields.Boolean('Hospitalización previa', tracking=True)
    x_parc_hosp_previa_especificar = fields.Char(string='Especificar', tracking=True)
    x_parc_ante_quir = fields.Boolean('Antecedentes quirúrgicos', tracking=True)
    x_parc_ante_quir_especificar = fields.Char(string='Especificar', tracking=True)
    x_parc_trans_previas = fields.Boolean('Transfusiones previas', tracking=True)
    x_parc_trans_previas_especificar = fields.Char(string='Especificar', tracking=True)
    x_parc_fracturas = fields.Boolean('Fracturas', tracking=True)
    x_parc_accidentes_traumatismos = fields.Boolean('Accidentes/traumatismo', tracking=True)
    x_parc_otra_enfermedad = fields.Boolean('Otra enfermedad', tracking=True)
    x_parc_otra_enfermedad_especificar = fields.Char(string='Especificar', tracking=True)
    x_parc_med_actuales = fields.Boolean('Medicamentos actuales', tracking=True)
    x_parc_med_actuales_especificar = fields.Char(string='Especificar', tracking=True)
    # Antecedentes gineco obstétricos
    x_gine_menarca = fields.Integer(string='Años de edad', tracking=True)
    x_gine_ciclos_reg = fields.Boolean('Ciclos regulares', tracking=True)
    x_gine_ritmo = fields.Char(string='Ritmo', tracking=True)
    x_gine_ultima_menstruacion = fields.Date(string='Fecha de última menstruación', tracking=True)
    x_gine_polimenorrea = fields.Boolean('Polimenorrea', tracking=True)
    x_gine_hipermenorrea = fields.Boolean('Hipermenorrea', tracking=True)
    x_gine_dismenorrea_incapacitante = fields.Boolean('Dismenorrea (incapacitante)', tracking=True)
    x_gine_ivsa = fields.Integer(string='Años', tracking=True)
    x_gine_parejas_sexuales = fields.Integer(string='Parejas sexuales', tracking=True)
    x_gine_g = fields.Char(string='G', tracking=True)
    x_gine_p = fields.Char(string='P', tracking=True)
    x_gine_a = fields.Char(string='A', tracking=True)
    x_gine_c = fields.Char(string='C', tracking=True)
    x_gine_fech_ult_citologia = fields.Date(string='Fecha de última citología(PAP)', tracking=True)
    x_gine_fech_ult_citologia_resultado = fields.Char(string='Resultado', tracking=True)
    x_gine_met_plani_familiar = fields.Selection([
        ('Anticonceptivos', 'Anticonceptivos'), ('Condón masculino', 'Condón masculino'),
        ('Condón femenino', 'Condón femenino'), ('Diafragma', 'Diafragma'), ('Intrauterinos', 'Intrauterinos'),
        ('Hormonas', 'Hormonas'), ('Ligadura', 'Ligadura'), ('Abstención', 'Abstención'), ('Otro', 'Otro'),
        ('Ninguno', 'Ninguno'), ('Sin especificar', 'Sin especificar')
    ], string='Tipo de planificación familiar', default='Sin especificar', tracking=True)
    # interrogatorio
    x_inter_res_cardio = fields.Char(string='Respiratorio/Cardiovascular', tracking=True)
    x_inter_digestivo = fields.Char(string='Digestivo', tracking=True)
    x_inter_endocrino = fields.Char(string='Endocrino', tracking=True)
    x_inter_musculo_esqueletico = fields.Char(string='Músculo-Esquelético', tracking=True)
    x_inter_genito_urirnario = fields.Char(string='Genito-Urinario', tracking=True)
    x_inter_hematopo_linfatico = fields.Char(string='Hematopoyético-Linfático', tracking=True)
    x_inter_piel_anexos = fields.Char(string='Piel y anexos', tracking=True)
    x_inter_neuro_psiquiatrico = fields.Char(string='Neurológico y Psiquiátrico', tracking=True)
    # Exploración
    x_explora_peso = fields.Integer(string='Peso (kgm)', tracking=True)
    x_explora_talla = fields.Integer(string='Talla (mts)', tracking=True)
    x_explora_ta = fields.Char(string='TA (mmHg)', tracking=True)
    x_explora_fc_pulso = fields.Integer(string='FC/Pulso (x min)', tracking=True)
    x_explora_fr = fields.Char(string='FR (x min)', tracking=True)
    x_explora_temp = fields.Integer(string='°C', tracking=True)
    x_explora_habitus = fields.Char(string='Habitus exterior', tracking=True)
    x_explora_piel_anexos = fields.Char(string='Piel y anexos', tracking=True)
    x_explora_cabeza_cuello = fields.Char(string='Cabeza y cuello', tracking=True)
    x_explora_torax = fields.Char(string='Tórax', tracking=True)
    x_explora_abdomen = fields.Char(string='Abdomen', tracking=True)
    x_explora_genitales = fields.Char(string='Genitales', tracking=True)
    x_explora_extremidades = fields.Char(string='Extremidades', tracking=True)
    x_explora_sis_nervioso = fields.Char(string='Sistema nervioso', tracking=True)
    x_explora_examen_previo = fields.Text(string='Exámenes de laboratorio previos', tracking=True)
    # Observaciones / comentarios finales
    x_observa_observa_comenta = fields.Text(string='Observaciones/Comentarios finales', tracking=True)
    # Integración diagnostica
    x_integra_diag_1 = fields.Char(string='Diagnostico 1', tracking=True)
    x_integra_diag_2 = fields.Char(string='Diagnostico 2', tracking=True)
    x_integra_diag_3 = fields.Char(string='Diagnostico 3', tracking=True)
    x_integra_diag_4 = fields.Char(string='Diagnostico 4', tracking=True)
    x_integra_plan_estudio_1 = fields.Char(string='Plan de estudio 1', tracking=True)
    x_integra_plan_estudio_2 = fields.Char(string='Plan de estudio 2', tracking=True)
    x_integra_plan_estudio_3 = fields.Char(string='Plan de estudio 3', tracking=True)
    x_integra_plan_estudio_4 = fields.Char(string='Plan de estudio 4', tracking=True)
    x_integra_plan_manejo_1 = fields.Char(string='Plan de manejo 1', tracking=True)
    x_integra_plan_manejo_2 = fields.Char(string='Plan de manejo 2', tracking=True)
    x_integra_plan_manejo_3 = fields.Char(string='Plan de manejo 3', tracking=True)
    x_integra_plan_manejo_4 = fields.Char(string='Plan de manejo 4', tracking=True)
    x_integra_pronostico = fields.Text(string='Pronóstico', tracking=True)
    x_integra_nombre_elaboro_historia = fields.Char(string='Nombre del médico que elaboró la historia', tracking=True)
    x_integra_nombre_avala_historia = fields.Char(string='Nombre del médico que avala la historia', tracking=True)

    # Verificar si tiene un evento abierto
    x_eventos_abiertos = fields.Integer(compute='_compute_eventos_abiertos', store=True)
    
    has_events = fields.Boolean(string='has events', compute='_compute_has_events')




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
            raise ValidationError(_('Existe un evento abierto y no se puede tener más de un evento abierto, cierra el evento anterior para continuar'))
        
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

    @api.depends('x_eventos_medicos_ids')
    def _compute_has_events(self):
        for partner in self:
            if partner.x_eventos_medicos_ids:
                partner.x_eventos_medicos_ids.search([()])
                partner.has_events = True
            else:
                partner.has_events = False