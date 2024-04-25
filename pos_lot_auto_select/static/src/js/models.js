odoo.define('pos_lot_auto_select.models', function(require){
	"use strict";
	// var screens = require('point_of_sale.screens');
	var core = require('web.core');
	var session = require('web.session');
	// var gui = require('point_of_sale.gui');
	var { Gui } = require('point_of_sale.Gui');
	var models = require('point_of_sale.models');
	// var PopupWidget = require('point_of_sale.popups');
	var QWeb = core.qweb;
	const Registries = require('point_of_sale.Registries');
	const ProductScreen = require('point_of_sale.ProductScreen');
	const OrderWidget = require('point_of_sale.OrderWidget');
	const EditListPopup = require('point_of_sale.EditListPopup');
	var { PosGlobalState, Order, Orderline } = require('point_of_sale.models');

	var utils = require('web.utils');

	var round_di = utils.round_decimals;
	var round_pr = utils.round_precision;

	const PosPosGlobalState = (PosGlobalState) => class PosPosGlobalState extends PosGlobalState {

		//@override
		async _processData(loadedData) {
			this.db.stock_quant = loadedData['stock.quant']['list_lot_stock_quant']
			this.db.list_lot_num = loadedData['stock.lot']['list_lot_num']
			this.list_lot_num_by_id = loadedData['stock.lot']['list_lot_num_by_id']
			this.list_lot_num_by_product_id = loadedData['stock.lot']['list_lot_num_by_product_id']
			this.db.pos_pack_lot_by_line_id = loadedData['pos.pack.operation.lot']
			await super._processData(...arguments);
		}

	  }
	  Registries.Model.extend(PosGlobalState, PosPosGlobalState);




	const PosOrderline = (Orderline) => class PosOrderline extends Orderline {
		export_as_JSON() {
			var json = super.export_as_JSON(...arguments);
			json.lot_details = this.get_order_line_lot();
			return json;
		}

		export_for_printing(){
			var pack_lot_ids = [];
			if (this.has_product_lot){
				this.pack_lot_lines.forEach(item => {
						return pack_lot_ids.push([0, 0, item.export_as_JSON()]);
				});

			}
			var data = super.export_for_printing(...arguments);
			data.pack_lot_ids = pack_lot_ids;
			data.lot_details = this.get_order_line_lot();

			return data;
		}

		get_order_line_lot(){
			var pack_lot_ids = [];
			if (this.has_product_lot){
				this.pack_lot_lines.forEach(item => {
						return pack_lot_ids.push([0, 0, item.export_as_JSON()]);
				});

			}
			return pack_lot_ids;
		}
		get_required_number_of_lots(){
			var lots_required = 1;

			if (this.product.tracking == 'serial' || this.product.tracking == 'lot') {
				lots_required = this.quantity * this.get_unit().factor_inv;
			}
			return lots_required;
		}

		can_be_merged_with(orderline){
			// override delete check if product tracking == "lot"
			var price = parseFloat(round_di(this.price || 0, this.pos.dp['Product Price']).toFixed(this.pos.dp['Product Price']));
			var order_line_price = orderline.get_product().get_price(orderline.order.pricelist, this.get_quantity());
			order_line_price = round_di(orderline.compute_fixed_price(order_line_price), this.pos.currency.decimal_places);
			if( this.get_product().id !== orderline.get_product().id){    //only orderline of the same product can be merged
					return false;
			}else if(!this.get_unit() || !this.get_unit().is_pos_groupable){
					return false;
			}else if(this.get_discount() > 0){             // we don't merge discounted orderlines
					return false;
			}else if(!utils.float_is_zero(price - order_line_price - orderline.get_price_extra(),
									this.pos.currency.decimal_places)){
					return false;
			}else if (this.description !== orderline.description) {
					return false;
			}else if (orderline.get_customer_note() !== this.get_customer_note()) {
					return false;
			} else if (this.refunded_orderline_id) {
					return false;
			}else{
					return true;
			}
		}

	}
	Registries.Model.extend(Orderline, PosOrderline);
	const PosOrder = (Order) => class PosOrder extends Order {
		async add_product(product, options){

			if (this.pos.config.allow_pos_lot && this.pos.config.allow_auto_select_lot && ['serial', 'lot'].includes(product.tracking) && (this.pos.picking_type.use_create_lots || this.pos.picking_type.use_existing_lots)) {

				const payload = await this._autoSelectLot(product,options);
				console.log('payload 1', payload );
				console.log('payload 2', payload.length );
				console.log('payload 3', Object.keys(payload));

				if (payload.length>0) {
					// console.log('confirmed',confirmed);
					console.log('payload 4',payload);

					const newPackLotLines = payload;
					const modifiedPackLotLines = [];
					options.draftPackLotLines = { modifiedPackLotLines, newPackLotLines };

					// draftPackLotLines = { payload };
				} else {
					// We don't proceed on adding product.
					return;
				}
			}
			super.add_product(...arguments);




    	}
		async _autoSelectLot(product,options) {
			console.log('##  _autoSelectLot  -->>  ' + product.id );			
			var self = this;
			let order = this.pos.get_order();
			let orderline = order.selected_orderline;

			const args = {};

			var qty  =  options.quantity || 1;
			if (orderline && orderline.product.id == product.id) {
				qty = orderline.get_quantity()+1;
			}

			var product_lot = [];
			var lot_list = [];
			var product_lots = this.pos.db.list_lot_num;

			var product_lot_stock_quant = this.pos.db.stock_quant;
			var pos_location_id = product_lot_stock_quant[0].location_id[0]

			for(var i=0;i<product_lots.length;i++){
				// console.log('##  product_lots first  -->>  ' + product_lots[i].product_id[0] + ' - ' + product_lots[i].name);			
				if(product_lots[i].product_id[0] == product.id){

					if (!product_lots[i]['expiration_date']) {
							var lot_expire_year = moment(new Date()).add(999,'y').format("YYYY-MM-DD HH:mm:ss");
							product_lots[i]['expiration_date'] = lot_expire_year;
					}

					for(var m=0;m<product_lot_stock_quant.length;m++){
						
						if(product_lot_stock_quant[m].location_id[0] == pos_location_id && product_lot_stock_quant[m].lot_id[0] == product_lots[i].id){
							product_lots[i]['temp_qty'] =  product_lot_stock_quant[m].quantity
							console.log('##  add_product  1a -->>  ' + product_lot_stock_quant[m].location_id[0] + ' - ' + m + ' - ' + product_lots[i].name);			
							lot_list.push(product_lots[i]);
						}
						console.log('##  add_product  1b -->>  ' + lot_list.length + ' - ' + product_lots[i].name );									
					}
				}
			}

			lot_list.sort((a, b) => (a.expiration_date > b.expiration_date) ? 1 : -1)

			if (product.is_controlled_product && (lot_list.length > 0)) {
				const LotListSelect = lot_list.map((product_id) => ({
					id: product_id.id,
					label: product_id.name,
					item: product_id,
				}));		
				
				console.log("LotListSelect:")
				console.log(LotListSelect);

				const { confirmed, payload: selectedlot } =  await Gui.showPopup('SelectionPopup', {
					title: ('Seleccione el numero de Lote'),
					list: LotListSelect ,
				});		
				if (confirmed) {
					args['product'] = selectedlot;
					console.log('Is Controlled  3 ' + Object.keys(selectedlot));	
					lot_list = []
					lot_list.push(args['product'])					
				}else{
					return false;
				}
			}
			if (product_lot.length>0){
				console.log('################       lot_list  2 -->>  ' + lot_list[0].name + ' - ' + lot_list[0].total_available_qty);
			}
			if (options.refunded_orderline_id) {
				var newPackLotLines = [];
				if (self.pos.db.pos_pack_lot_by_line_id[options.refunded_orderline_id]) {
					self.pos.db.pos_pack_lot_by_line_id[options.refunded_orderline_id].forEach(function(pack_lot){
						let obj = { lot_name: pack_lot.lot_name  , prod_qty : -1};
						for(var m=0;m<product_lot_stock_quant.length;m++){
							console.log('##  add_product   2 -->>  ' + product_lot_stock_quant[m].location_id[0]);			
							if(product_lot_stock_quant[m].location_id[0] == pos_location_id){
								newPackLotLines.push(obj);
							}
						}						
						
					});
				}else {
					alert("You can`t refund order from same session");

				}
				return newPackLotLines;
			}else {
				console.log('##  add_product  3a -->>  ' + lot_list.length);
				
				for(var i=0;i<lot_list.length;i++){
					console.log('##  add_product  3b -->>  ' + lot_list[i].name + '  +  ' + lot_list[i].product_id[1]  + ' -  ' + lot_list[i].temp_qty  );			
					if(lot_list[i].product_id[0] == product.id){
						for(var m=0;m<product_lot_stock_quant.length;m++){
							if(product_lot_stock_quant[m].location_id[0] == pos_location_id && product_lot_stock_quant[m].product_id[0] == lot_list[i].product_id[0] && product_lot_stock_quant[m].lot_id[0] == lot_list[i].id){
								lot_list[i]['temp_qty'] =  product_lot_stock_quant[m].quantity
								console.log('##  add_product  3c -->>  ' + product_lot_stock_quant[m].quantity );			
								product_lot.push(lot_list[i]);

							}
						}						
					}
				}
				product_lot.sort((a, b) => (a.expiration_date > b.expiration_date) ? 1 : -1);

				let selected_lots = [];
				console.log('##  add_product 3d product_lot -->>  ' + product_lot.length);							
				
				if (product_lot.length>0) {
					var qty_temp = qty;
					var i =0;


					while (qty_temp>0  ) {
						if (product_lot.length<= i) {
							alert("Not enough Lot");
							break;
						}
						let obj = {};

						if(product_lot[i]['temp_qty'] >= qty_temp){
							// lot_list[i]['temp_qty'] =  lot_list[i].product_qty
							// obj[product_lot[i].id] = qty_temp;
							obj = {id: product_lot[i].id ,name:product_lot[i].name ,qty : qty_temp}
							qty_temp =0;
						}else if (product_lot[i]['temp_qty']<qty_temp) {
							obj = {id: product_lot[i].id ,name:product_lot[i].name ,qty : product_lot[i]['temp_qty']}
							qty_temp -=product_lot[i]['temp_qty'];
							// obj[product_lot[i].id] = product_lot[i]['temp_qty'];
						}
						i+=1;
						selected_lots.push(obj);
					}

					for (var j = 0; j < selected_lots.length; j++) {
						for(var i=0;i<lot_list.length;i++){
							if(lot_list[i].id == selected_lots[j].id){
								if (lot_list[i]['temp_qty'] <= 0) {
									alert("Not enough qty !!");
								}
								lot_list[i]['temp_qty'] -=selected_lots[j].qty
								console.log('##  temp_qty selected_lots -->>  ' + lot_list[i]['temp_qty']);
							}
						}
					}

					console.log('##  add_product 4a selected_lots -->>  ' + selected_lots.length);							
					var newPackLotLines = [];
					for (var j = 0; j < selected_lots.length; j++) {
						for (var i = 0; i < selected_lots[j].qty; i++) {
							let obj = { lot_name: selected_lots[j].name  , prod_qty : 1};
							console.log('##  add_product 4b -->>  ' + selected_lots[j].name);
							newPackLotLines.push(obj);
							
						}
					}

					return newPackLotLines;
				}
				else if (product_lot.length>0 && product.is_controlled_product){
					var qty_temp = qty;
					var i =0;


					while (qty_temp>0  ) {
						if (product_lot.length<= i) {
							alert("Not enough Lot");
							break;
						}
						let obj = {};

						if(product_lot[i]['temp_qty'] >= qty_temp){
							// lot_list[i]['temp_qty'] =  lot_list[i].product_qty
							// obj[product_lot[i].id] = qty_temp;
							obj = {id: product_lot[i].id ,name:product_lot[i].name ,qty : qty_temp}
							qty_temp =0;
						}else if (product_lot[i]['temp_qty']<qty_temp) {
							obj = {id: product_lot[i].id ,name:product_lot[i].name ,qty : product_lot[i]['temp_qty']}
							qty_temp -=product_lot[i]['temp_qty'];
							// obj[product_lot[i].id] = product_lot[i]['temp_qty'];
						}
						i+=1;
						selected_lots.push(obj);
					}

					for (var j = 0; j < selected_lots.length; j++) {
						for(var i=0;i<lot_list.length;i++){
							if(lot_list[i].id == selected_lots[j].id){
								if (lot_list[i]['temp_qty'] <= 0) {
									alert("Not enough qty !!");
								}
								lot_list[i]['temp_qty'] -=selected_lots[j].qty
								console.log('##  temp_qty selected_lots -->>  ' + lot_list[i]['temp_qty']);
							}
						}
					}

					console.log('##  add_product 4a selected_lots -->>  ' + selected_lots.length);							
					var newPackLotLines = [];
					for (var j = 0; j < selected_lots.length; j++) {
						for (var i = 0; i < selected_lots[j].qty; i++) {
							let obj = { lot_name: selected_lots[j].name  , prod_qty : 1};
							console.log('##  add_product 4b -->>  ' + selected_lots[j].name);
							newPackLotLines.push(obj);
							
						}
					}

					return newPackLotLines;					
				}
				else {
					alert("Not enough qty !!");
				}
			}

			return [];
		}
	}
	Registries.Model.extend(Order, PosOrder);


});