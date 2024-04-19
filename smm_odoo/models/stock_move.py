from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

from collections import defaultdict

from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from odoo.tools.misc import clean_context, OrderedSet


class StockMove(models.Model):
    _inherit = 'stock.move'

    is_controlled_product = fields.Boolean(
        string = 'Es producto controlado'
        , related = 'product_id.is_controlled_product'
        , store = True
    )

    def _search_picking_for_assignation(self):
        self.ensure_one()

        domain = [
            ('group_id', '=', self.group_id.id)
            , ('location_id', '=', self.location_id.id)
            , ('location_dest_id', '=', self.location_dest_id.id)
            , ('picking_type_id', '=', self.picking_type_id.id)
            , ('scheduled_date', '=', self.date)
            , ('printed', '=', False)
            , ('immediate_transfer', '=', False)
            , ('state', 'in', ['draft', 'confirmed', 'waiting', 'partially_available', 'assigned'])
        ]

        if self.partner_id and (self.location_id.usage == 'transit' or self.location_dest_id.usage == 'transit'):
            domain += [('partner_id', '=', self.partner_id.id)]

        picking = self.env['stock.picking'].search(domain, limit = 1)

        return picking

    def write(self, vals):
        # Handle the write on the initial demand by updating the reserved quantity and logging
        # messages according to the state of the stock.move records.
        receipt_moves_to_reassign = self.env['stock.move']
        move_to_recompute_state = self.env['stock.move']
        if 'quantity_done' in vals and any(move.state == 'cancel' for move in self):
            raise UserError(_('You cannot change a cancelled stock move, create a new line instead.'))
        if 'product_uom' in vals and any(move.state == 'done' for move in self):
            raise UserError(_('You cannot change the UoM for a stock move that has been set to \'Done\'.'))
        if 'product_uom_qty' in vals:
            move_to_unreserve = self.env['stock.move']
            for move in self.filtered(lambda m: m.state not in ('done', 'draft') and m.picking_id):
                if float_compare(vals['product_uom_qty'], move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                    self.env['stock.move.line']._log_message(move.picking_id, move, 'stock.track_move_template', vals)
            if self.env.context.get('do_not_unreserve') is None:
                move_to_unreserve = self.filtered(
                    lambda m: m.state not in ['draft', 'done', 'cancel'] and float_compare(m.reserved_availability, vals.get('product_uom_qty'), precision_rounding=m.product_uom.rounding) == 1
                )
                move_to_unreserve._do_unreserve()
                (self - move_to_unreserve).filtered(lambda m: m.state == 'assigned').write({'state': 'partially_available'})
                # When editing the initial demand, directly run again action assign on receipt moves.
                receipt_moves_to_reassign |= move_to_unreserve.filtered(lambda m: m.location_id.usage == 'supplier')
                receipt_moves_to_reassign |= (self - move_to_unreserve).filtered(lambda m: m.location_id.usage == 'supplier' and m.state in ('partially_available', 'assigned'))
                move_to_recompute_state |= self - move_to_unreserve - receipt_moves_to_reassign
        # propagate product_packaging_id changes in the stock move chain
        if 'product_packaging_id' in vals:
            self._propagate_product_packaging(vals['product_packaging_id'])
        if 'date_deadline' in vals:
            self._set_date_deadline(vals.get('date_deadline'))
        res = super(StockMove, self).write(vals)
        if move_to_recompute_state:
            move_to_recompute_state._recompute_state()
        # if receipt_moves_to_reassign:
        #     receipt_moves_to_reassign._action_assign()
        return res

    def _action_confirm(self, merge=True, merge_into=False):
        """ Confirms stock move or put it in waiting if it's linked to another move.
        :param: merge: According to this boolean, a newly confirmed move will be merged
        in another move of the same picking sharing its characteristics.
        """
        # Use OrderedSet of id (instead of recordset + |= ) for performance
        move_create_proc, move_to_confirm, move_waiting = OrderedSet(), OrderedSet(), OrderedSet()
        to_assign = defaultdict(OrderedSet)
        for move in self:
            if move.state != 'draft':
                continue
            # if the move is preceded, then it's waiting (if preceding move is done, then action_assign has been called already and its state is already available)
            if move.move_orig_ids:
                move_waiting.add(move.id)
            else:
                if move.procure_method == 'make_to_order':
                    move_create_proc.add(move.id)
                else:
                    move_to_confirm.add(move.id)
            if move._should_be_assigned():
                key = (move.group_id.id, move.location_id.id, move.location_dest_id.id)
                to_assign[key].add(move.id)

        move_create_proc, move_to_confirm, move_waiting = self.browse(move_create_proc), self.browse(move_to_confirm), self.browse(move_waiting)

        # create procurements for make to order moves
        procurement_requests = []
        for move in move_create_proc:
            values = move._prepare_procurement_values()
            origin = move._prepare_procurement_origin()
            procurement_requests.append(self.env['procurement.group'].Procurement(
                move.product_id, move.product_uom_qty, move.product_uom,
                move.location_id, move.rule_id and move.rule_id.name or "/",
                origin, move.company_id, values))
        self.env['procurement.group'].run(procurement_requests, raise_user_error=not self.env.context.get('from_orderpoint'))

        move_to_confirm.write({'state': 'confirmed'})
        (move_waiting | move_create_proc).write({'state': 'waiting'})
        # procure_method sometimes changes with certain workflows so just in case, apply to all moves
        (move_to_confirm | move_waiting | move_create_proc).filtered(lambda m: m.picking_type_id.reservation_method == 'at_confirm')\
            .write({'reservation_date': fields.Date.today()})

        # assign picking in batch for all confirmed move that share the same details
        for moves_ids in to_assign.values():
            self.browse(moves_ids).with_context(clean_context(self.env.context))._assign_picking()
        new_push_moves = self.filtered(lambda m: not m.picking_id.immediate_transfer)._push_apply()
        self._check_company()
        moves = self
        if merge:
            moves = self._merge_moves(merge_into=merge_into)

        # Transform remaining move in return in case of negative initial demand
        neg_r_moves = moves.filtered(lambda move: float_compare(
            move.product_uom_qty, 0, precision_rounding=move.product_uom.rounding) < 0)
        for move in neg_r_moves:
            move.location_id, move.location_dest_id = move.location_dest_id, move.location_id
            orig_move_ids, dest_move_ids = [], []
            for m in move.move_orig_ids | move.move_dest_ids:
                from_loc, to_loc = m.location_id, m.location_dest_id
                if float_compare(m.product_uom_qty, 0, precision_rounding=m.product_uom.rounding) < 0:
                    from_loc, to_loc = to_loc, from_loc
                if to_loc == move.location_id:
                    orig_move_ids += m.ids
                elif move.location_dest_id == from_loc:
                    dest_move_ids += m.ids
            move.move_orig_ids, move.move_dest_ids = [(6, 0, orig_move_ids)], [(6, 0, dest_move_ids)]
            move.product_uom_qty *= -1
            if move.picking_type_id.return_picking_type_id:
                move.picking_type_id = move.picking_type_id.return_picking_type_id
            # We are returning some products, we must take them in the source location
            move.procure_method = 'make_to_stock'
        neg_r_moves._assign_picking()

        # call `_action_assign` on every confirmed move which location_id bypasses the reservation + those expected to be auto-assigned
        # moves.filtered(lambda move: not move.picking_id.immediate_transfer
        #                and move.state in ('confirmed', 'partially_available')
        #                and (move._should_bypass_reservation()
        #                     or move.picking_type_id.reservation_method == 'at_confirm'
        #                     or (move.reservation_date and move.reservation_date <= fields.Date.today())))\
        #      ._action_assign()
        if new_push_moves:
            neg_push_moves = new_push_moves.filtered(lambda sm: float_compare(sm.product_uom_qty, 0, precision_rounding=sm.product_uom.rounding) < 0)
            (new_push_moves - neg_push_moves)._action_confirm()
            # Negative moves do not have any picking, so we should try to merge it with their siblings
            neg_push_moves._action_confirm(merge_into=neg_push_moves.move_orig_ids.move_dest_ids)

        return moves
