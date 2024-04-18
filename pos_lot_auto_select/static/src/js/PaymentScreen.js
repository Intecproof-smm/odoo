odoo.define('pos_lot_auto_select.PaymentScreen', function(require){
	'use strict';

	const PaymentScreen = require('point_of_sale.PaymentScreen');
	const Registries = require('point_of_sale.Registries');

	const PaymentScreenExtend = (PaymentScreen) => class PaymentScreenExtend extends PaymentScreen {

		async validateOrder(isForceValidate) {
			var self = this;
			var order = this.env.pos.get_order();
			var orderline = order.get_orderlines();
			var lot_list = this.env.pos.db.list_lot_num;
			orderline.forEach(function(line) {
				if(line.has_product_lot){

					line.pack_lot_lines.forEach(function(lot){
						lot_list.forEach(function(d_lot){
							if(line.product.id == d_lot.product_id[0] && d_lot.name == lot.lot_name){
								if (order.is_return_order) {
									d_lot.total_available_qty = d_lot.total_available_qty + 1
								}else {
									d_lot.total_available_qty = d_lot.total_available_qty - 1
								}
							}

						});
					});
				}
			});
			super.validateOrder(isForceValidate);
		}
	}
	Registries.Component.extend(PaymentScreen, PaymentScreenExtend);


	return PaymentScreen;

});
