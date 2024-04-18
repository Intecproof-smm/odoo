/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define("pos_product_by_lot_number.ProductScreen", function (require) {
	"use strict";
	const ProductScreen = require('point_of_sale.ProductScreen');
	const Registries = require('point_of_sale.Registries');
	const NumberBuffer = require('point_of_sale.NumberBuffer');
	const { isConnectionError } = require('point_of_sale.utils');
	const { ConnectionLostError, ConnectionAbortedError } = require('@web/core/network/rpc_service');
	const { identifyError } = require('point_of_sale.utils');

	const PosProductScreen = (ProductScreen) =>
		class extends ProductScreen {
			_setValue(val) {
				var self = this;
				var order = self.env.pos.get_order();
				var selected_orderline = order.get_selected_orderline();
				var lot = self.env.pos.db.lot_no;
				if (selected_orderline) {
					var mode = self.env.pos.numpadMode;
					if (mode === 'quantity') {
						if (selected_orderline.has_product_lot && selected_orderline.pack_lot_lines[0]) {
							var lot_name = selected_orderline.pack_lot_lines[0]["lot_name"];
							var is_lot = _.find(lot, function (num) {
								return num.name == lot_name;
							});
							var count = order.product_total_by_lot(lot_name) + parseInt(val) - selected_orderline.quantity;
							if (is_lot && (val > lot[lot_name].product_qty || count > lot[lot_name].product_qty)) {
								var value = this.env.pos.get_order().get_remaining_products(lot_name);
								this.showPopup("WkLSAlertPopUp", {
									'title': 'Out Of Quantity!',
									'body': "Maximum products available to add in Lot/Serial Number " + lot_name + " are " + value + "."
								});
								NumberBuffer.reset();
							} else {
								super._setValue(val);
							}
						} else {
							super._setValue(val);
						}
					} else {
						super._setValue(val);
					}
				}
			}
			async _barcodeProductAction(code) {
				var self = this;
				var product = this.env.pos.db.get_product_by_barcode(code.base_code);
				if (!product) {
					var data = self.env.pos.db.lot_no[code.base_code];
					if (data) {
						if (data.product_id) {
							var lot_product = data.product_id;
							var wk_product = self.env.pos.db.product_by_id[lot_product[0]]
							if (!wk_product){
								// find the barcode in the backend
								let foundProductIds = [];
								try {
									foundProductIds = await this.rpc({
										model: 'product.product',
										method: 'search',
										args: [[['id', '=', lot_product[0]]]],
										context: this.env.session.user_context,
									});
								} catch (error) {
									if (isConnectionError(error)) {
										return this.showPopup('OfflineErrorPopup', {
											title: this.env._t('Network Error'),
											body: this.env._t("Product is not loaded. Tried loading the product from the server but there is a network error."),
										});
									} else {
										throw error;
									}
								}
								if (foundProductIds.length) {
									await this.env.pos._addProducts(foundProductIds);
									// assume that the result is unique.
									wk_product = this.env.pos.db.get_product_by_id(foundProductIds[0]);
								} else {
									return this._barcodeErrorAction(code);
								}
							}
							const options = await this._getAddProductOptions(wk_product, code);
							if (!options) return;
							// update the options depending on the type of the scanned code
							if (code.type === 'price') {
								Object.assign(options, {
									price: code.value,
									extras: {
										price_manually_set: true,
									},
								});
							} else if (code.type === 'weight') {
								Object.assign(options, {
									quantity: code.value,
									merge: false,
								});
							} else if (code.type === 'discount') {
								Object.assign(options, {
									discount: code.value,
									merge: false,
								});
							}
							this.env.pos.get_order().add_product(wk_product, {
								scan: true,
								lot_name: code.base_code,
								draftPackLotLines:options.draftPackLotLines,
							});
							return true
						}
					} else {
						super._barcodeProductAction(code);
					}
				} else {
					super._barcodeProductAction(code);
				}
			}
			async _getAddProductOptions(product, base_code) {
				if(base_code && base_code == 'lot'){
					let price_extra = 0.0;
					let draftPackLotLines, weight, description, packLotLinesToEdit;
					if(product)
						if (_.some(product.attribute_line_ids, (id) => id in this.env.pos.attributes_by_ptal_id)) {
							let attributes = _.map(product.attribute_line_ids, (id) => this.env.pos.attributes_by_ptal_id[id])
											.filter((attr) => attr !== undefined);
							let { confirmed, payload } = await this.showPopup('ProductConfiguratorPopup', {
								product: product,
								attributes: attributes,
							});
							if (confirmed) {
								description = payload.selected_attributes.join(', ');
								price_extra += payload.price_extra;
							} else {
								return;
							}
						}
					// Gather lot information if required.
					if (product)
						if (['serial', 'lot'].includes(product.tracking) && (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots)) {
							const isAllowOnlyOneLot = product.isAllowOnlyOneLot();
							if (isAllowOnlyOneLot) {
								packLotLinesToEdit = [];
							} else {
								const orderline = this.currentOrder
									.get_orderlines()
									.filter(line => !line.get_discount())
									.find(line => line.product.id === product.id);
								if (orderline) {
									packLotLinesToEdit = orderline.getPackLotLinesToEdit();
								} else {
									packLotLinesToEdit = [];
								}
							}

							// const { confirmed, payload } = await this.showPopup('EditListPopup', {
							// 	title: this.env._t('Lot/Serial Number(s) Required'),
							// 	isSingleItem: isAllowOnlyOneLot,
							// 	array: packLotLinesToEdit,
							// 	product:product,
							// });

							var payload = {
								newArray:[{
									text:base_code.base_code,
									_id:base_code.value
								}]
							}

							if (payload) {
								// Segregate the old and new packlot lines
								const modifiedPackLotLines = Object.fromEntries(
									payload.newArray.filter(item => item.id).map(item => [item.id, item.text])
								);

								const newPackLotLines = payload.newArray
									.filter(item => !item.id)
									.map(item => ({ lot_name: item.text }));

								draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
							} else {
								// We don't proceed on adding product.
								return;
							}
						}

					// Take the weight if necessary.
					if (product.to_weight && this.env.pos.config.iface_electronic_scale) {
						// Show the ScaleScreen to weigh the product.
						if (this.isScaleAvailable) {
							const { confirmed, payload } = await this.showTempScreen('ScaleScreen', {
								product,
							});
							if (confirmed) {
								weight = payload.weight;
							} else {
								// do not add the product;
								return;
							}
						} else {
							await this._onScaleNotAvailable();
						}
					}

					if (base_code && this.env.pos.db.product_packaging_by_barcode[base_code.code]) {
						weight = this.env.pos.db.product_packaging_by_barcode[base_code.code].qty;
					}

					return { draftPackLotLines, quantity: weight, description, price_extra };	 
				} else {
					return super._getAddProductOptions(product, base_code);
				}
			}
			async _clickProduct(event) {
				var self = this;
				let price_extra = 0.0;
				let packLotLinesToEdit, draftPackLotLines,description,weight;
				const product = event.detail;
				// Gather lot information if required.
				if (['serial', 'lot'].includes(product.tracking)) {
					const isAllowOnlyOneLot = product.isAllowOnlyOneLot();
					if (isAllowOnlyOneLot) {
						packLotLinesToEdit = [];
					} else {
						const orderline = this.currentOrder
							.get_orderlines()
							.filter(line => !line.get_discount())
							.find(line => line.product.id === product.id);

						if (orderline) {
							packLotLinesToEdit = orderline.getPackLotLinesToEdit();
						} else {
							packLotLinesToEdit = [];
						}
					}
					const {
						confirmed,
						payload
					} = await this.showPopup('EditListPopup', {
						title: this.env._t('Lot/Serial Number(s) Required'),
						isSingleItem: isAllowOnlyOneLot,
						array: packLotLinesToEdit,
						product:product,

					});
					if (confirmed) {
						// Segregate the old and new packlot lines
						const modifiedPackLotLines = Object.fromEntries(
							payload.newArray.filter(item => item.id).map(item => [item.id, item.text])
						);
						const newPackLotLines = payload.newArray
							.filter(item => !item.id)
							.map(item => ({
								lot_name: item.text
							}));

						draftPackLotLines = {
							modifiedPackLotLines,
							newPackLotLines
						};
					} else {
						// We don't proceed on adding product.
						return;
					}
					// Take the weight if necessary.
					if (product.to_weight && this.env.pos.config.iface_electronic_scale) {
						// Show the ScaleScreen to weigh the product.
						if (this.isScaleAvailable) {
							const { confirmed, payload } = await this.showTempScreen('ScaleScreen', {
								product,
							});
							if (confirmed) {
								weight = payload.weight;
							} else {
								// do not add the product;
								return;
							}
						} else {
							await this._onScaleNotAvailable();
						}
					}

					// Add the product after having the extra information.
					this.currentOrder.add_product(product, {
						draftPackLotLines,
						description: description,
						price_extra: price_extra,
						quantity: weight,
					});
					NumberBuffer.reset();
				}
				else{
					super._clickProduct(event)
				}
			}
		}

	Registries.Component.extend(ProductScreen, PosProductScreen);
	return ProductScreen;
});
