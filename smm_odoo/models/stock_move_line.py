from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero

import json

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    picking_type_id_domain = fields.Char(string = "Dominio por Tipo de Operacion", readonly = True, store = True, compute='compute_move_id_picking_type_id_domain')

    @api.depends('move_id.picking_type_id','product_id','company_id','location_id')
    def compute_move_id_picking_type_id_domain(self):
        for record in self:
            if record.move_id.picking_type_id.id != 1:
                record.picking_type_id_domain = json.dumps([('product_id', '=', record.product_id.id),('company_id', '=', record.company_id.id),('location_ids', 'in', record.location_id.id)])
            else:
                record.picking_type_id_domain = json.dumps([('product_id', '=', record.product_id.id),('company_id', '=', record.company_id.id)])

    def write(self, vals):
        if self.env.context.get('bypass_reservation_update'):
            return super(StockMoveLine, self).write(vals)

        if 'product_id' in vals and any(vals.get('state', ml.state) != 'draft' and vals['product_id'] != ml.product_id.id for ml in self):
            raise UserError(_("Changing the product is only allowed in 'Draft' state."))

        moves_to_recompute_state = self.env['stock.move']
        Quant = self.env['stock.quant']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        triggers = [
            ('location_id', 'stock.location'),
            ('location_dest_id', 'stock.location'),
            ('lot_id', 'stock.lot'),
            ('package_id', 'stock.quant.package'),
            ('result_package_id', 'stock.quant.package'),
            ('owner_id', 'res.partner'),
            ('product_uom_id', 'uom.uom')
        ]
        updates = {}
        for key, model in triggers:
            if key in vals:
                updates[key] = vals[key] if isinstance(vals[key], models.BaseModel) else self.env[model].browse(vals[key])

        if 'result_package_id' in updates:
            for ml in self.filtered(lambda ml: ml.package_level_id):
                if updates.get('result_package_id'):
                    ml.package_level_id.package_id = updates.get('result_package_id')
                else:
                    # TODO: make package levels less of a pain and fix this
                    package_level = ml.package_level_id
                    ml.package_level_id = False
                    # Only need to unlink the package level if it's empty. Otherwise will unlink it to still valid move lines.
                    if not package_level.move_line_ids:
                        package_level.unlink()

        # When we try to write on a reserved move line any fields from `triggers` or directly
        # `reserved_uom_qty` (the actual reserved quantity), we need to make sure the associated
        # quants are correctly updated in order to not make them out of sync (i.e. the sum of the
        # move lines `reserved_uom_qty` should always be equal to the sum of `reserved_quantity` on
        # the quants). If the new charateristics are not available on the quants, we chose to
        # reserve the maximum possible.
        if updates or 'reserved_uom_qty' in vals:
            for ml in self.filtered(lambda ml: ml.state in ['partially_available', 'assigned'] and ml.product_id.type == 'product'):

                if 'reserved_uom_qty' in vals:
                    new_reserved_uom_qty = ml.product_uom_id._compute_quantity(
                        vals['reserved_uom_qty'], ml.product_id.uom_id, rounding_method='HALF-UP')
                    # Make sure `reserved_uom_qty` is not negative.
                    if float_compare(new_reserved_uom_qty, 0, precision_rounding=ml.product_id.uom_id.rounding) < 0:
                        raise UserError(_('Reserving a negative quantity is not allowed.'))
                else:
                    new_reserved_uom_qty = ml.reserved_qty

                # Unreserve the old charateristics of the move line.
                if not ml.move_id._should_bypass_reservation(ml.location_id):
                    Quant._update_reserved_quantity(ml.product_id, ml.location_id, -ml.reserved_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)

                # Reserve the maximum available of the new charateristics of the move line.
                if not ml.move_id._should_bypass_reservation(updates.get('location_id', ml.location_id)):
                    reserved_qty = 0
                    try:
                        q = Quant._update_reserved_quantity(ml.product_id, updates.get('location_id', ml.location_id), new_reserved_uom_qty, lot_id=updates.get('lot_id', ml.lot_id),
                                                            package_id=updates.get('package_id', ml.package_id), owner_id=updates.get('owner_id', ml.owner_id), strict=True)
                        reserved_qty = sum([x[1] for x in q])
                    except UserError:
                        pass
                    if reserved_qty != new_reserved_uom_qty:
                        new_reserved_uom_qty = ml.product_id.uom_id._compute_quantity(reserved_qty, ml.product_uom_id, rounding_method='HALF-UP')
                        moves_to_recompute_state |= ml.move_id
                        ml.with_context(bypass_reservation_update=True).reserved_uom_qty = new_reserved_uom_qty
                        # we don't want to override the new reserved quantity
                        vals.pop('reserved_uom_qty', None)

        # When editing a done move line, the reserved availability of a potential chained move is impacted. Take care of running again `_action_assign` on the concerned moves.
        if updates or 'qty_done' in vals:
            next_moves = self.env['stock.move']
            mls = self.filtered(lambda ml: ml.move_id.state == 'done' and ml.product_id.type == 'product')
            if not updates:  # we can skip those where qty_done is already good up to UoM rounding
                mls = mls.filtered(lambda ml: not float_is_zero(ml.qty_done - vals['qty_done'], precision_rounding=ml.product_uom_id.rounding))
            for ml in mls:
                # undo the original move line
                qty_done_orig = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                in_date = Quant._update_available_quantity(ml.product_id, ml.location_dest_id, -qty_done_orig, lot_id=ml.lot_id,
                                                    package_id=ml.result_package_id, owner_id=ml.owner_id)[1]
                Quant._update_available_quantity(ml.product_id, ml.location_id, qty_done_orig, lot_id=ml.lot_id,
                                                    package_id=ml.package_id, owner_id=ml.owner_id, in_date=in_date)

                # move what's been actually done
                product_id = ml.product_id
                location_id = updates.get('location_id', ml.location_id)
                location_dest_id = updates.get('location_dest_id', ml.location_dest_id)
                qty_done = vals.get('qty_done', ml.qty_done)
                lot_id = updates.get('lot_id', ml.lot_id)
                package_id = updates.get('package_id', ml.package_id)
                result_package_id = updates.get('result_package_id', ml.result_package_id)
                owner_id = updates.get('owner_id', ml.owner_id)
                product_uom_id = updates.get('product_uom_id', ml.product_uom_id)
                quantity = product_uom_id._compute_quantity(qty_done, ml.move_id.product_id.uom_id, rounding_method='HALF-UP')
                if not ml.move_id._should_bypass_reservation(location_id):
                    ml._free_reservation(product_id, location_id, quantity, lot_id=lot_id, package_id=package_id, owner_id=owner_id)
                if not float_is_zero(quantity, precision_digits=precision):
                    available_qty, in_date = Quant._update_available_quantity(product_id, location_id, -quantity, lot_id=lot_id, package_id=package_id, owner_id=owner_id)
                    if available_qty < 0 and lot_id:
                        # see if we can compensate the negative quants with some untracked quants
                        untracked_qty = Quant._get_available_quantity(product_id, location_id, lot_id=False, package_id=package_id, owner_id=owner_id, strict=True)
                        if untracked_qty:
                            taken_from_untracked_qty = min(untracked_qty, abs(available_qty))
                            Quant._update_available_quantity(product_id, location_id, -taken_from_untracked_qty, lot_id=False, package_id=package_id, owner_id=owner_id)
                            Quant._update_available_quantity(product_id, location_id, taken_from_untracked_qty, lot_id=lot_id, package_id=package_id, owner_id=owner_id)
                            if not ml.move_id._should_bypass_reservation(location_id):
                                ml._free_reservation(ml.product_id, location_id, untracked_qty, lot_id=False, package_id=package_id, owner_id=owner_id)
                    Quant._update_available_quantity(product_id, location_dest_id, quantity, lot_id=lot_id, package_id=result_package_id, owner_id=owner_id, in_date=in_date)

                # Unreserve and reserve following move in order to have the real reserved quantity on move_line.
                next_moves |= ml.move_id.move_dest_ids.filtered(lambda move: move.state not in ('done', 'cancel'))

                # Log a note
                if ml.picking_id:
                    ml._log_message(ml.picking_id, ml, 'stock.track_move_template', vals)

        res = super(StockMoveLine, self).write(vals)

        # As stock_account values according to a move's `product_uom_qty`, we consider that any
        # done stock move should have its `quantity_done` equals to its `product_uom_qty`, and
        # this is what move's `action_done` will do. So, we replicate the behavior here.
        if updates or 'qty_done' in vals:
            moves = self.filtered(lambda ml: ml.move_id.state == 'done').mapped('move_id')
            moves |= self.filtered(lambda ml: not ml.move_id.origin_returned_move_id and ml.move_id.state not in ('done', 'cancel')\
                and ml.move_id.picking_id.immediate_transfer).mapped('move_id')
            for move in moves:
                move.product_uom_qty = move.quantity_done
            next_moves._do_unreserve()
            # next_moves._action_assign()

        if moves_to_recompute_state:
            moves_to_recompute_state._recompute_state()

        return res
