import logging
from odoo import fields, models
from odoo.exceptions import UserError
from datetime import datetime

_logger = logging.getLogger(__name__)


class StockPickingButtonAssignWizard(models.TransientModel):
    _name = 'stock.picking.button.assign.wizard'
    _description = 'Stock picking button assign wizard'

    stock_picking_id = fields.Many2one(
        'stock.picking'
        , string = 'Stock picking to assign'
        , required = True
    )
#creacion de lineas para sugerir en automatico lote deacuerdo a fecha de caducidad
# siendo el primero el mas proximo a caducar y como ultima opcion el caducado 13102022
    def confirm_action_assign(self):
        self.ensure_one()

        current_user = self.env['res.users'].browse(self.env.user.id)
        _logger.info('Comprobando disponibilidad de albarán - ' + str(current_user.login))

        for line in self.stock_picking_id.move_line_ids_without_package:
            line.unlink()

        for line in self.stock_picking_id.move_ids_without_package:
            cantidad_restante = line.product_uom_qty
            inventarios = self.env['stock.quant'].search([('product_id','=',line.product_id.id),('location_id','=',self.stock_picking_id.location_id.id)])
            lotes_inventarios = []
            for inventario in inventarios:
                if inventario.available_quantity > 0:
                    lotes_inventarios.append(inventario.lot_id.id)
            lotes_sin_expirar = self.env['stock.lot'].search([('product_id','=',line.product_id.id), ('expiration_date','>=',datetime.now()), ('id','in',lotes_inventarios)], order = 'expiration_date asc')
            for lote in lotes_sin_expirar:
                for inventario in inventarios:
                    if inventario.lot_id.id == lote.id:
                        if inventario.available_quantity >= cantidad_restante:
                            nueva_linea = {
                                'picking_id': self.stock_picking_id.id,
                                'move_id': line.id,
                                'company_id': self.stock_picking_id.company_id.id,
                                'product_id': line.product_id.id,
                                'location_id': self.stock_picking_id.location_id.id,
                                'location_dest_id':self.stock_picking_id.location_dest_id.id,
                                'lot_id': lote.id,
                                'reserved_uom_qty': cantidad_restante,
                                'qty_done': cantidad_restante,
                                'product_uom_id': line.product_id.uom_id.id
                            }
                            ml = self.env['stock.move.line'].create(nueva_linea)
                            self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, cantidad_restante, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                            cantidad_restante = 0
                        else:
                            nueva_linea = {
                                'picking_id': self.stock_picking_id.id,
                                'move_id': line.id,
                                'company_id': self.stock_picking_id.company_id.id,
                                'product_id': line.product_id.id,
                                'location_id': self.stock_picking_id.location_id.id,
                                'location_dest_id': self.stock_picking_id.location_dest_id.id,
                                'lot_id': lote.id,
                                'reserved_uom_qty': inventario.available_quantity,
                                'qty_done': inventario.available_quantity,
                                'product_uom_id': line.product_id.uom_id.id
                            }
                            ml = self.env['stock.move.line'].create(nueva_linea)
                            cantidad_restante = cantidad_restante - inventario.available_quantity
                            self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, inventario.available_quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                if cantidad_restante == 0:
                    break
            if cantidad_restante > 0:
                lotes_expirados = self.env['stock.lot'].search([('product_id','=',line.product_id.id), ('expiration_date','<',datetime.now()), ('id','in',lotes_inventarios)], order = 'expiration_date desc')
                for lote in lotes_expirados:
                    for inventario in inventarios:
                        if inventario.lot_id.id == lote.id:
                            if inventario.available_quantity >= cantidad_restante:
                                nueva_linea = {
                                    'picking_id': self.stock_picking_id.id,
                                    'move_id': line.id,
                                    'company_id': self.stock_picking_id.company_id.id,
                                    'product_id': line.product_id.id,
                                    'location_id': self.stock_picking_id.location_id.id,
                                    'location_dest_id': self.stock_picking_id.location_dest_id.id,
                                    'lot_id': lote.id,
                                    'reserved_uom_qty': cantidad_restante,
                                    'qty_done': cantidad_restante,
                                'product_uom_id': line.product_id.uom_id.id
                                }
                                ml = self.env['stock.move.line'].create(nueva_linea)
                                self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, cantidad_restante, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                                cantidad_restante = 0
                            else:
                                nueva_linea = {
                                    'picking_id': self.stock_picking_id.id,
                                    'move_id': line.id,
                                    'company_id': self.stock_picking_id.company_id.id,
                                    'product_id': line.product_id.id,
                                    'location_id': self.stock_picking_id.location_id.id,
                                    'location_dest_id': self.stock_picking_id.location_dest_id.id,
                                    'lot_id': lote.id,
                                    'reserved_uom_qty': inventario.available_quantity,
                                    'qty_done': inventario.available_quantity,
                                'product_uom_id': line.product_id.uom_id.id
                                }
                                ml = self.env['stock.move.line'].create(nueva_linea)
                                cantidad_restante = cantidad_restante - inventario.available_quantity
                                self.env['stock.quant']._update_reserved_quantity(ml.product_id, ml.location_id, inventario.available_quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
                    if cantidad_restante == 0:
                        break

        # METODO BASE
        """ Check availability of picking moves.
        This has the effect of changing the state and reserve quants on available moves, and may
        also impact the state of the picking as it is computed based on move's states.
        @return: True
        """
        self.stock_picking_id.filtered(lambda picking: picking.state == 'draft').action_confirm()
        #_logger(str(self.stock_picking_id))

        moves = self.stock_picking_id.mapped('move_ids').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))

        if not moves:
            raise UserError(_('Nothing to check the availability for.'))
        # If a package level is done when confirmed its location can be different than where it will be reserved.
        # So we remove the move lines created when confirmed to set quantity done to the new reserved ones.
        package_level_done = self.stock_picking_id.mapped('package_level_ids').filtered(
            lambda pl: pl.is_done and pl.state == 'confirmed'
        )
        package_level_done.write({'is_done': False})
        moves._action_assign()
        package_level_done.write({'is_done': True})

        for move in self.stock_picking_id.move_ids_without_package:
            producto_encontrado = False
            for linea in self.stock_picking_id.move_line_ids_without_package:
                if linea.product_id.id == move.product_id.id:
                    producto_encontrado = True
            if not producto_encontrado:
                move.state = 'waiting'

        return True