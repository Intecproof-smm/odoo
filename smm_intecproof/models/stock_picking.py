from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero

###################################################################################
#
#    Copyright (c) 2023-today Jaime López y Azael
#
#    This file is part of SMM_intecproof Module
#
#    This program is NOT a free software
#
#    Aplicación para añadir las opciones T Y O y Anestesio al campo de opcion x_area_solicitud
#    y añade la opción JF al campo de opción x_turno
###################################################################################


class stock_pickin_anade_opciones(models.Model):
    _inherit = 'stock.picking'
    
    x_area_solicitud = fields.Selection(
        selection=[
            ('urg', 'Urgencias')
            , ('hp', 'Hospital')
            , ('cons', 'Consulta')
            , ('uci', 'UCI')
            , ('quir', 'Quirofano')
            , ('ph', 'Prehospitalario')
            , ('tyo', 'T y O')
            , ('anes', 'Anestesio')
        ]
        , string='Área que solicita'
        , store=True
    )

    x_turno = fields.Selection(
        selection=[
            ('m', 'M')
            , ('v', 'V')
            , ('n1', 'N1')
            , ('n2', 'N2')
            , ('ja', 'JA')
            , ('jf', 'JF')
        ]
        , string='Turno'
        , store=True
    )

    x_receta = fields.Char(string = 'Receta', store = True)
    x_indicacion = fields.Char(string = 'Indicación', store = True)
    x_medico = fields.Char(string = 'Médico', store = True)

    def _prepare_picking_vals(self, partner, picking_type, location_id, location_dest_id, datos_salida):
        return {
            'partner_id': partner.id if partner else False
            , 'user_id': False
            , 'picking_type_id': picking_type.id
            , 'move_type': 'direct'
            , 'location_id': location_id
            , 'location_dest_id': location_dest_id
            , 'x_area_solicitud': datos_salida['area_solicitud']
            , 'x_cama': datos_salida['cama']
            , 'x_fecha_nacimiento': datos_salida['fecha_nacimiento']
            , 'x_no_ambulancia': datos_salida['no_ambulancia']
            , 'x_solicitante': datos_salida['solicitante'].id if datos_salida['solicitante'] else False
            , 'x_turno': datos_salida['turno']
            , 'x_receta': datos_salida['receta']
            , 'x_indicacion': datos_salida['indicacion']
            , 'x_medico': datos_salida['medico']
            , 'has_controlled_product': datos_salida['has_controlled_product']
        }

    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False, datos_salida=False):
        """We'll create some picking based on order_lines"""

        pickings = self.env['stock.picking']
        stockable_lines = lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding))
        if not stockable_lines:
            return pickings
        positive_lines = stockable_lines.filtered(lambda l: l.qty > 0)
        negative_lines = stockable_lines - positive_lines

        if positive_lines:
            location_id = picking_type.default_location_src_id.id
            positive_picking = self.env['stock.picking'].create(
                self._prepare_picking_vals(partner, picking_type, location_id, location_dest_id, datos_salida)
            )

            positive_picking._create_move_from_pos_order_lines(positive_lines)
            self.env.flush_all()
            try:
                with self.env.cr.savepoint():
                    positive_picking._action_done()
            except (UserError, ValidationError):
                pass

            pickings |= positive_picking
        if negative_lines:
            if picking_type.return_picking_type_id:
                return_picking_type = picking_type.return_picking_type_id
                return_location_id = return_picking_type.default_location_dest_id.id
            else:
                return_picking_type = picking_type
                return_location_id = picking_type.default_location_src_id.id

            negative_picking = self.env['stock.picking'].create(
                self._prepare_picking_vals(partner, return_picking_type, location_dest_id, return_location_id, datos_salida)
            )
            negative_picking._create_move_from_pos_order_lines(negative_lines)
            self.env.flush_all()
            try:
                with self.env.cr.savepoint():
                    negative_picking._action_done()
            except (UserError, ValidationError):
                pass
            pickings |= negative_picking
        return pickings
