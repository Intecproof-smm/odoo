odoo.define('pos_product_by_lot_number.EditListInput', function(require) {
    'use strict';
    const EditListInput = require('point_of_sale.EditListInput');
    const Registries = require('point_of_sale.Registries');

    const PosEditListInput = (EditListInput) =>
      class extends EditListInput {
        onKeyup(event) {
            super.onKeyup(event);
        }
      }
    Registries.Component.extend(EditListInput, PosEditListInput);
    return EditListInput;  
});
