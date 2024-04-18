odoo.define('pos_lot_selection_ucs.ProductScreen', function (require) {
    'use strict';
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const UCSProductScreen = (ProductScreen) => class UCSProductScreen extends ProductScreen {   
        async _getAddProductOptions(product, base_code) {
            let price_extra = 0.0;
            let draftPackLotLines, weight, description, packLotLinesToEdit;
            var usedPackLotLines = [];
            const selectedOrder = this.env.pos.get_order();
            if (this.env.pos.config.product_configurator && _.some(product.attribute_line_ids, (id) => id in this.env.pos.attributes_by_ptal_id)) {
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

            if (product.to_weight && this.env.pos.config.iface_electronic_scale) {
                if (this.isScaleAvailable) {
                    const { confirmed, payload } = await this.showTempScreen('ScaleScreen', {
                        product,
                    });
                    if (confirmed) {
                        weight = payload.weight;
                    } else {
                        return;
                    }
                } else {
                    await this._onScaleNotAvailable();
                }
            }

            if (base_code && this.env.pos.db.product_packaging_by_barcode[base_code.code]) {
                weight = this.env.pos.db.product_packaging_by_barcode[base_code.code].qty;
            }
            if (['serial', 'lot'].includes(product.tracking) && (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots)) {
                const isAllowOnlyOneLot = product.isAllowOnlyOneLot();
                let draftPackLotLines;
                var  lotNameList = []
                let existingLots = await this.rpc({
                    model: 'stock.lot',
                    method: 'search_read',
                    domain: [['product_id', '=', product.id],['product_qty', '>', 0]],
                    fields: []
                }).then(function (value) {
                    return value
                }, function (error) {
                    return false
                })
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
                packLotLinesToEdit.forEach((l) => l.text = l.name);
                if(packLotLinesToEdit.length > 0){
                    packLotLinesToEdit = packLotLinesToEdit.filter(function(item) {
                      if (item.text == undefined)
                        return false;
                      else
                        return true;
                    });
                }
                _.each(selectedOrder.get_orderlines(),function(orl){
                	if (orl.product.tracking != 'none'){
                		usedPackLotLines.push(orl.getPackLotLinesToEdit());
                	}
                });
                var usedPackLotLinesDict = {}
                if(usedPackLotLines.length > 0){
                    _.each(usedPackLotLines,function(opl){
                        _.each(opl,function(ulot){
                            if( ulot.text in usedPackLotLinesDict){
                                usedPackLotLinesDict[ulot.text] += 1
                            }
                            else{
                                usedPackLotLinesDict[ulot.text] = 1
                            }
                        });
                    });
                }
                if(existingLots.length > 0){
                    existingLots = existingLots.filter(function(x){
                            return x.product_qty > 0;
                     })
                }
                const lotList = existingLots.map(l => ({
                    id: l.id,
                    item: l,
                    label: l.name,
                    qty : (usedPackLotLinesDict && l.name in usedPackLotLinesDict) ? l.product_qty -  usedPackLotLinesDict[l.name]: l.product_qty ,
                    expiration_date : (l.expiration_date || 'N/A'),
                    is_expired : l.is_expired,
                    used_qty : packLotLinesToEdit.filter(function(x){
                        return x.text === l.name;
                    }).length,
                }))
                lotNameList = existingLots.map(l => (l.name))
                console.log("Lot List---",lotList)
                if (lotList.length > 0) {

                    const {confirmed, payload} = await this.showPopup('EditListPopup', {
                        title: this.env._t('Lot/Serial Number(s) Required'),
                        isSingleItem: false,
                        array: packLotLinesToEdit,
                        lotList:lotList,
                        product:product,
                        lotNameList:lotNameList,
                    });
                    if (confirmed) {
//                            
                        const modifiedPackLotLines = Object.fromEntries(
                            payload.newArray.filter(item => item.id).map(item => [item.id, item.text])
                        );
                        const newPackLotLines = payload.newArray
                            .filter(item => !item.id)
                            .map(item => ({ lot_name: item.text  , prod_qty : item.qty}));
                        draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
                        return await selectedOrder.add_product(product, {
                            draftPackLotLines,
                            price_extra:price_extra,
                            description:description,
                            quantity: weight,
                        })
                    }
                }
                else{
                    if(this.env.pos.config.restrict_out_of_stock){
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Lot/Serial Not Found'),
                            body: this.env._t('Lot/Serial Number is not found for selected products!'),
                        });
                        return false;
                    }
                }
            }

            return { draftPackLotLines, quantity: weight, description, price_extra };
        }
    }
    Registries.Component.extend(ProductScreen, UCSProductScreen);
    return UCSProductScreen;
});
