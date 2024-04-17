odoo.define('pos_lot_selection_ucs.OrderWidget', function(require){
    var core = require('web.core');
    var models = require('point_of_sale.models');
    var QWeb = core.qweb;
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const OrderWidget = require('point_of_sale.OrderWidget');
    const EditListPopup = require('point_of_sale.EditListPopup');
    const UCSOrderWidget = (OrderWidget) =>
        class extends OrderWidget {
            async _editPackLotLines(event) {
                const orderline = event.detail.orderline;
                const isAllowOnlyOneLot = orderline.product.isAllowOnlyOneLot();
                const packLotLinesToEdit = orderline.getPackLotLinesToEdit(false);
                var usedPackLotLines = [];
                _.each(this.order.get_orderlines(),function(orl){
                    if(orl.id != orderline.id && orl.product.tracking != 'none'){
                        usedPackLotLines.push(orl.getPackLotLinesToEdit());
                    }
                });
//                
                var lotList = [];
                var lotNameList = [];

                let existingLots = await this.rpc({
                    model: 'stock.lot',
                    method: 'search_read',
                    domain: [['product_id', '=', orderline.product.id],['product_qty', '>', 0]],
                    fields: []
                }).then(function (value) {
                    return value
                }, function (error) {
                    return false
                })
                if(existingLots.length > 0){
                    existingLots = existingLots.filter(function(x){
                            return x.product_qty > 0;
                     })
                }

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
                    lotList = existingLots.map(l => ({
                        id: l.id,
                        item: l,
                        label: l.name,
                        qty : (usedPackLotLinesDict && l.name in usedPackLotLinesDict) ? l.product_qty -  usedPackLotLinesDict[l.name]: l.product_qty ,
                        used_qty : packLotLinesToEdit.filter(function(x){
                            return x.text === l.name;
                        }).length,
                        expiration_date : (l.expiration_date || 'N/A'),
                        is_expired : l.is_expired
                    }))
                    lotNameList = existingLots.map(l => (l.name))
                }
                const { confirmed, payload } = await this.showPopup('EditListPopup', {
                    title: this.env._t('Lot/Serial Number(s) Required'),
                    isSingleItem: isAllowOnlyOneLot,
                    array: packLotLinesToEdit,
                    product: orderline.product,
                    lotList:lotList,
                    lotNameList:lotNameList,
                });
                if (confirmed) {

//                    
                    const modifiedPackLotLines = Object.fromEntries(
                        payload.newArray.filter(item => item.id).map(item => [item.id, item.text])
                    );
                    const newPackLotLines = payload.newArray
                        .filter(item => !item.id)
                        .map(item => ({ lot_name: item.text , prod_qty : item.qty}));
                    orderline.setPackLotLines({ modifiedPackLotLines, newPackLotLines });
                }
                this.order.select_orderline(event.detail.orderline);
            }
        };

    Registries.Component.extend(OrderWidget, UCSOrderWidget);

    return UCSOrderWidget;
 });
