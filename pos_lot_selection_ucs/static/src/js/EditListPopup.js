odoo.define('pos_lot_selection_ucs.EditListPopup', function(require) {
    'use strict';

    const { useState } = owl;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
//    const { useAutoFocus ToLast } = require('point_of_sale.custom_hooks');
    const { _lt } = require('@web/core/l10n/translation');
    const EditListPopup = require('point_of_sale.EditListPopup')

    const PosEditListPopup = EditListPopup => class extends EditListPopup {
        get barcodes(){
            return this.props.barcodes;
        }
        addNewLotLine(event){
            var self = this;
            var max_quantity_to_use = $(event.target).attr('lot-qty');
            let entered_item_qty = $(event.target).find('input');
            let entered_qty = parseFloat($(event.target).val());
            if(entered_qty > max_quantity_to_use){
                $(event.target).css({"border" : '1px solid red'})
                return false
            }
            else{
                $(event.target).css({"border" : 'none'})
            }

            var lot_id = $(event.target).attr('lot-id');
            _.each(self.props.lotList, function(lot) {
                if (lot_id == lot.id){
                    lot.used_qty = entered_qty
                }
            });
            self.state.array = self.state.array.filter(function( obj ) {
              return obj.text !== $(event.target).attr('lot-name');
            });

            for(var i = 0 ; i < entered_qty ; i++){
                self.state.array.push(
                    {text: $(event.target).attr('lot-name'),
                    qty : 1,
                    _id: self._nextId(),
                });
            }
        }
    };

    Registries.Component.extend(EditListPopup, PosEditListPopup);

    return PosEditListPopup;


});
