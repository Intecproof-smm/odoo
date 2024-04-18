# -*- coding: utf-8 -*-
from odoo import api,fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare
from itertools import groupby

class StockProductionLot(models.Model):

    _inherit = 'stock.lot'

    is_expired = fields.Boolean(string='is Expired', compute='compute_is_expired')

    def compute_is_expired(self):
        for rec in self:
            current_datetime = fields.Datetime.context_timestamp(rec, fields.Datetime.now())
            if rec.expiration_date:
                expiry_datetime = fields.Datetime.context_timestamp(rec, rec.expiration_date)
                rec.is_expired = expiry_datetime < current_datetime
            else:
                rec.is_expired = False


class PosConfig(models.Model):

    _inherit = 'pos.config'

    restrict_out_of_stock = fields.Boolean(string='Restrict Adding Products?')


class PosOrder(models.Model):

    _inherit = 'pos.order'

    def get_available_lots(self,product_id):
        lot_ids = self.env['product.product'].search([('product_id','=',product_id)])
        available_lots = {}
        for lot in lot_ids:
            if lot.product_qty > 0:
                reserved_qty = 0
                quants = lot.quant_ids.filtered(lambda q: q.location_id.usage in ['internal', 'transit'])
                for q in quants:
                    reserved_qty += q.reserved_quantity
                available_qty = lot.product_qty - reserved_qty
                if available_qty > 0:
                    available_lots.update({'id' : lot.id,'name' : lot.name,'quantity' : lot.quantity})
        return available_lots


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    def _create_move_from_pos_order_lines(self, lines):
        self.ensure_one()
        lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id), key=lambda l: l.product_id.id)
        for product, lines in lines_by_product:
            order_lines = self.env['pos.order.line'].concat(*lines)
            first_line = order_lines[0]
            current_move = self.env['stock.move'].create(
                self._prepare_stock_move_vals(first_line, order_lines)
            )
            confirmed_moves = current_move._action_confirm()
            for move in confirmed_moves:
                if first_line.product_id == move.product_id and first_line.product_id.tracking != 'none':
                    if self.picking_type_id.use_existing_lots or self.picking_type_id.use_create_lots:
                        for line in order_lines:
                            sum_of_lots = 0
                            for lot in line.pack_lot_ids.filtered(lambda l: l.lot_name):
                                if line.product_id.tracking == 'serial':
                                    qty = 1
                                else:
                                    qty = abs(1)
                                ml_vals = move._prepare_move_line_vals()
                                ml_vals.update({'qty_done':qty})
                                if self.picking_type_id.use_existing_lots:
                                    existing_lot = self.env['stock.lot'].search([
                                        ('company_id', '=', self.company_id.id),
                                        ('product_id', '=', line.product_id.id),
                                        ('name', '=', lot.lot_name)
                                    ])
                                    if not existing_lot and self.picking_type_id.use_create_lots:
                                        existing_lot = self.env['stock.lot'].create({
                                            'company_id': self.company_id.id,
                                            'product_id': line.product_id.id,
                                            'name': lot.lot_name,
                                        })
                                    quant = existing_lot.quant_ids.filtered(lambda q: q.quantity > 0.0 and q.location_id.parent_path.startswith(move.location_id.parent_path))[-1:]
                                    ml_vals.update({
                                        'lot_id': existing_lot.id,
                                        'location_id': quant.location_id.id or move.location_id.id
                                    })
                                else:
                                    ml_vals.update({
                                        'lot_name': lot.lot_name,
                                    })
                                self.env['stock.move.line'].create(ml_vals)
                                sum_of_lots += qty
                            if abs(line.qty) != sum_of_lots:
                                difference_qty = abs(line.qty) - sum_of_lots
                                ml_vals = current_move._prepare_move_line_vals()
                                if line.product_id.tracking == 'serial':
                                    ml_vals.update({'qty_done': 1})
                                    for i in range(int(difference_qty)):
                                        self.env['stock.move.line'].create(ml_vals)
                                else:
                                    ml_vals.update({'qty_done': difference_qty})
                                    self.env['stock.move.line'].create(ml_vals)
                    else:
                        move._action_assign()
                        for move_line in move.move_line_ids:
                            move_line.qty_done = move_line.product_uom_qty
                        if float_compare(move.product_uom_qty, move.quantity_done, precision_rounding=move.product_uom.rounding) > 0:
                            remaining_qty = move.product_uom_qty - move.quantity_done
                            ml_vals = move._prepare_move_line_vals()
                            ml_vals.update({'qty_done':remaining_qty})
                            self.env['stock.move.line'].create(ml_vals)

                else:
                    move._action_assign()
                    for move_line in move.move_line_ids:
                        move_line.qty_done = move_line.product_uom_qty
                    if float_compare(move.product_uom_qty, move.quantity_done, precision_rounding=move.product_uom.rounding) > 0:
                        remaining_qty = move.product_uom_qty - move.quantity_done
                        ml_vals = move._prepare_move_line_vals()
                        ml_vals.update({'qty_done':remaining_qty})
                        self.env['stock.move.line'].create(ml_vals)
                    move.quantity_done = move.product_uom_qty
