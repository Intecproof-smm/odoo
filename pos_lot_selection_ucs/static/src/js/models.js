odoo.define('pos_lot_selection_ucs.model', function(require){

    var { Orderline, Product } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    const ProductInh = (Product) => class ProductInh extends Product {
        isAllowOnlyOneLot() {
            const productUnit = this.get_unit();
            return this.tracking === 'serial' || !productUnit || !productUnit.is_pos_groupable;
        }
    }

    Registries.Model.extend(Product, ProductInh);

    const OrderlineInh = (Orderline) => class OrderlineInh extends Orderline {
        get_required_number_of_lots(){
            return Math.abs(this.quantity);
        }
    }
    Registries.Model.extend(Orderline, OrderlineInh);

});
