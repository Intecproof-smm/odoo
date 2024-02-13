# -*- coding: utf-8 -*-
from odoo import models, fields, api

# Clase que extende el modelo pos.order para agregar propiedades que se 
# necesitan para las salidas de inventario
class PosOrder(models.Model):
    _inherit = "pos.order"

    x_area_solicitud = fields.Selection(
        selection = [
            ('urg', 'Urgencias')
            , ('hp', 'Hospital')
            , ('cons', 'Consulta')
            , ('uci', 'UCI')
            , ('quir', 'Quirofano')
            , ('tyo', 'T y O')
            , ('ane', 'Anestesio')
        ]
        , string = 'Área que solicita'
        , store = True
    )

    x_cama = fields.Char(string = 'Cama', store = True)

    x_fecha_nacimiento = fields.Date(
        string = 'Fecha de nacimiento',
        related = 'partner_id.x_fecha_nacimiento',
        store = True
    )

    x_no_ambulancia = fields.Char(string = 'Ambulancia', store = True)

    x_solicitante = fields.Many2one('res.partner', string = 'Solicitante', store = True)

    x_turno = fields.Selection(
        selection = [
            ('m', 'M')
            , ('v', 'V')
            , ('n1', 'N1')
            , ('n2', 'N2')
            , ('ja', 'JA')
            , ('jf', 'JF')
        ]
        , string = 'Turno'
        , store = True
    )

    x_expediente = fields.Char(string = 'Expediente', store = True)

    x_diagnostico = fields.Char(string = 'Diagnóstico', store = True)

    x_dosis_aplicada = fields.Char(string = 'Dosis aplicada', store = True)

    x_via_aplicacion = fields.Selection(
        selection = [
            ('iv', 'IV'),
            ('sc', 'SC'),
            ('im', 'IM')
        ]
        , string = 'Vía'
        , store = True
    )

    x_indicacion = fields.Char(string = 'Indicación', store = True)

    @api.model
    def _order_fields(self, ui_order):
        order = super()._order_fields(ui_order)
        order['x_area_solicitud'] = ui_order['x_area_solicitud']
        order['x_cama'] = ui_order['x_cama']
        order['x_fecha_nacimiento'] = self.partner_id.x_fecha_nacimiento
        order['x_no_ambulancia'] = ui_order['x_no_ambulancia']
        # El solicitante se va a capturar mediante la tarjeta
        # order['x_solicitante'] = ui_order['x_solicitante']['id'] or False
        order['x_turno'] = ui_order['x_turno']
        order['x_expediente'] = ui_order['x_expediente']
        order['x_diagnostico'] = ui_order['x_diagnostico']
        order['x_dosis_aplicada'] = ui_order['x_dosis_aplicada']
        order['x_via_aplicacion'] = ui_order['x_via_aplicacion']
        order['x_indicacion'] = ui_order['x_indicacion']
        return order
    
    def _create_order_picking(self):
        has_controlled_product = False
        self.ensure_one()
        if self.to_ship:
            self.lines._launch_stock_rule_from_pos_order_lines()
        else:
            if self._should_create_picking_real_time():
                picking_type = self.config_id.picking_type_id
                if self.partner_id.property_stock_customer:
                    destination_id = self.partner_id.property_stock_customer.id
                elif not picking_type or not picking_type.default_location_dest_id:
                    destination_id = self.env['stock.warehouse']._get_partner_locations()[0].id
                else:
                    destination_id = picking_type.default_location_dest_id.id

                productos_controlados = self.lines.filtered(lambda l: l.product_id.is_controlled_product == True)
                if productos_controlados:
                    has_controlled_product = True

                datos_salida = {
                    'area_solicitud': self.x_area_solicitud
                    , 'cama': self.x_cama
                    , 'fecha_nacimiento': self.x_fecha_nacimiento
                    , 'no_ambulancia': self.x_no_ambulancia
                    , 'solicitante': self.x_solicitante
                    , 'turno': self.x_turno
                    , 'has_controlled_product': has_controlled_product
                }

                pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(destination_id, self.lines, picking_type, self.partner_id, datos_salida)
                pickings.write({'pos_session_id': self.session_id.id, 'pos_order_id': self.id, 'origin': self.name})
