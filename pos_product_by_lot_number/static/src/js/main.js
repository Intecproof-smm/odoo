/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
odoo.define("pos_product_by_lot_number", function(require) {
  "use strict";
  const { Gui } = require('point_of_sale.Gui');
  const { _t } = require('web.core');
  const PaymentScreen = require('point_of_sale.PaymentScreen');
  const Registries = require('point_of_sale.Registries');
  var { PosGlobalState, Order,Packlotline,Orderline} = require('point_of_sale.models');
  var PosDB = require('point_of_sale.DB');

  const PosLotNumberGlobalState = (PosGlobalState) => class PosLotNumberGlobalState extends PosGlobalState {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.db._loadStockLot(loadedData['stock.lot'])
    }
    // ---------Make it Compatible with Pos Stock----------
    async _addProducts(ids, setAvailable=true){
      if(setAvailable){
          await this.env.services.rpc({
              model: 'product.product',
              method: 'write',
              args: [ids, {'available_in_pos': true}],
              context: this.env.session.user_context,
          });
      }
      let product = await this.env.services.rpc({
          model: 'pos.session',
          method: 'get_pos_ui_product_product_by_params',
          args: [odoo.pos_session_id, {domain: [['id', 'in', ids]]}],
      });
      // ---------Make it Compatible with Pos Stock----------Used Await
      await this._loadProductProduct(product);
    }
  }
  Registries.Model.extend(PosGlobalState, PosLotNumberGlobalState);

  PosDB.include({
    _loadStockLot: function(lots){
      var self = this;
      self.lot_no = {};
      self.product_by_id_lot_no = {};
      if(lots){
        _.each(lots, function(lot) {
          self.lot_no[lot.name] = lot;
          if (lot.product_id[0] in self.product_by_id_lot_no){
            self.product_by_id_lot_no[lot.product_id[0]].push(lot.name)
          }else{
            self.product_by_id_lot_no[lot.product_id[0]] = [lot.name]
          }
        });
      }
    },
  })

    var productByLotOrder = (Order) =>
      class extends Order{
      // add_product_by_type is used to add product
      add_product_by_type(product, options) {
          if(this._printed){
            // when adding product with a barcode while being in receipt screen
            this.pos.removeOrder(this);
            return this.pos.add_new_order().add_product(product, options);
          }
          this.assert_editable();
          options = options || {};
          var line = Orderline.create({}, {pos: this.pos, order: this, product: product});
          this.fix_tax_included_price(line);

          if(options.quantity !== undefined){
              line.set_quantity(options.quantity);
          }
  
          if (options.price_extra !== undefined){
              line.price_extra = options.price_extra;
              line.set_unit_price(line.product.get_price(this.pricelist, line.get_quantity(), options.price_extra));
              this.fix_tax_included_price(line);
          }

          if(options.price !== undefined){
              line.set_unit_price(options.price);
              this.fix_tax_included_price(line);
          }

          if(options.lst_price !== undefined){
              line.set_lst_price(options.lst_price);
          }

          if(options.discount !== undefined){
              line.set_discount(options.discount);
          }

          if (options.description !== undefined){
              line.description += options.description;
          }

          if(options.extras !== undefined){
              for (var prop in options.extras) {
                  line[prop] = options.extras[prop];
              }
          }

          if (options.is_tip) {
              this.is_tipped = true;
              this.tip_amount = options.price;
          }

          var to_merge_orderline;
          for (var i = 0; i < this.orderlines.length; i++) {
              if(this.orderlines.at(i).can_be_merged_with(line) && options.merge !== false){
                  to_merge_orderline = this.orderlines.at(i);
              }
          }
          if (to_merge_orderline){
              to_merge_orderline.merge(line);
              this.select_orderline(to_merge_orderline);
          } else {
              this.orderlines.add(line);
              this.select_orderline(this.get_last_orderline());
          }

          if (this.pos.config.iface_customer_facing_display) {
              this.pos.send_current_order_to_customer_facing_display();
          }
          this.select_orderline(this.get_last_orderline());
          // options.draftPackLotLines.newPackLotLines.push({'lot_name':options.lot_name})
          if(options['draftPackLotLines'] && options['draftPackLotLines']['newPackLotLines']){
            var newPackLotLines = [{'lot_name':options['draftPackLotLines']['newPackLotLines'][0].lot_name}];
          }
          var modifiedPackLotLines = [];
          // this.selected_orderline.setPackLotLines({modifiedPackLotLines,newPackLotLines});
          // --------------------------------------------------------------------------------
          let newPackLotLine;
          if(newPackLotLines){
            for (let newLotLine of newPackLotLines) {
                newPackLotLine = new Packlotline({}, { order_line: this });
                newPackLotLine['lot_name'] = newLotLine.lot_name;
                this.selected_orderline.pack_lot_lines.add(newPackLotLine);
            }
          }
          // Set the quantity of the line based on number of pack lots.
          if(this.selected_orderline && this.selected_orderline.pack_lot_lines){
              this.wk_set_quantity_by_lot(this.selected_orderline.pack_lot_lines);
          }
          // --------------------------------------------------------------------------------
      }
      wk_set_quantity_by_lot(line){
        var self = this;
        if (line.lot_name){
          var lot = self.env.pos.db.lot_no[line.pack_lot_lines.lot_name]
          var sel_orderline = self.env.pos.get_order().selected_orderline;
          if(sel_orderline.quantity <= lot.product_qty){
            sel_orderline.set_quantity(sel_orderline.quantity);
          }
        }
      }
      product_total_by_lot(lot_name){
        var self = this;
        var count = 0;
        var lot = this.pos.db.lot_no[lot_name]
        if(self.pos && self.pos.orders){
          _.each(self.pos.orders, function(order) {
            _.each(order.get_orderlines(), function(orderline) {
              if (lot && orderline.pack_lot_lines && lot.product_id[0] == orderline.product.id) {
                _.each(orderline.pack_lot_lines, function(packlot) {
                  if (packlot["lot_name"] == lot_name) {
                    count += orderline.quantity;
                  }
                });
              }
            });
          });
        }
        return count
      }
      product_total_by_serial(lot_name,orderline_id) {
        var count = 0;
        var lot = this.pos.db.lot_no[lot_name]
        _.each(this.pos.get('orders').models, function(order) {
          _.each(order.get_orderlines(), function(orderline) {
            if (lot && orderline.pack_lot_lines && orderline.id != orderline_id && lot.product_id[0] == orderline.product.id && orderline.product.tracking == 'serial') {
              _.each(orderline.pack_lot_lines.models, function(packlot) {
                if (packlot.attributes["lot_name"] == lot_name) {
                  count += 1;
                }
              });
            }
          });
        });
        return count
      }
      //get_remanining_products is use to calculate the remaining items in lot once the error popup.
      get_remaining_products(lot_name) {
        var lot = this.pos.db.lot_no[lot_name]
        if (lot) {
          var remaining_qty = lot.product_qty - this.product_total_by_lot(lot_name);
          // var remaining_qty = lot.product_qty - this.product_total_by_lot(lot_name) + this.pos.get_order().get_selected_orderline().quantity
        }
        return remaining_qty
      }
      add_product(product, options) {
        var qty = null;
        var quant = null;
        if (options && product) {
          if(options.lot_name){
              qty = this.pos.db.lot_no[options.lot_name].product_qty;
              quant = this.product_total_by_lot(options.lot_name);
          } else {
            if(options['draftPackLotLines'] && options['draftPackLotLines']['newPackLotLines'] ){
              qty = this.pos.db.lot_no[options['draftPackLotLines']['newPackLotLines'][0].lot_name].product_qty
              quant = this.product_total_by_lot(options['draftPackLotLines']['newPackLotLines'][0].lot_name);
            }
          }

          if(product.tracking){
            var tracking = product.tracking;
            var wk_lot_name = null;
            if (options['draftPackLotLines'] && options['draftPackLotLines']['newPackLotLines']){
              wk_lot_name = options['draftPackLotLines']['newPackLotLines'][0] ;
            }
            
            var lot_name = options.lot_name || wk_lot_name;
            if (tracking == "lot") {
              if(quant > qty){
                Gui.showPopup('WkLSAlertPopUp', {
                  title: "Lot Is Empty!",
                  'body': "The quantity of selected product in lot " + lot_name + " is Zero."
                });
              } else {
                this.add_product_by_type(product, options)
              }
            } else if (tracking == "serial") {
              if (quant < qty && quant < 1) {
                this.add_product_by_type(product, options)
              } else {
                Gui.showPopup('WkLSAlertPopUp', {
                  title: "Serial Number!",
                  'body': "Only one product can be added by using serial number " + options.lot_name + "."
                });
              }
            } else {
              super.add_product(product, options)
            }
          } else {
            super.add_product(product, options)
          }

        } else {
          super.add_product(product, options)
        }
      }
      //wk_add_lot automatically allots the scanned lot/serial number to the product in orderline
      wk_add_lot(options) {
        var order_line = this.get_selected_orderline();
        var pack_lot_lines = order_line.compute_lot_lines();
        if(pack_lot_lines._byId){
          var pack_lot_lines_keys  = Object.keys(pack_lot_lines._byId);
          if(pack_lot_lines_keys && pack_lot_lines_keys.length > 0){
            var cid = pack_lot_lines_keys[pack_lot_lines_keys.length - 1];
            var lot_name = options["lot_name"];
            var pack_line = pack_lot_lines.get({ cid: cid });
            if(pack_line && lot_name)
              pack_line.set_lot_name(lot_name);
          }
          pack_lot_lines.set_quantity_by_lot();
          this.save_to_db();
          order_line.trigger('change', order_line);
        }
      }
  };
  Registries.Model.extend(Order, productByLotOrder);

  const PosResPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
          async validateOrder(isForceValidate) {
            var res = super.validateOrder(isForceValidate);
            var self = this;
            var order = self.env.pos.get_order()
            res.then(() => {
              if (order.finalized)
                self.update_lot_by_orderline();
            })
          }
          update_lot_by_orderline() {
            var self = this;
            // Client has many products and lots( in lakhs) and was facing hanging issue on validation
            // in our code we were looping over all the lots(large no) and then again looping over orderlines and then on packlotlines(O(n^3)) and this needs optimization

            //  optimization :
            // I had created an object of product_id : lots in db as key:value pair ---> product_by_id_lot_no
            // by this we can get access to the lots associated with a product
            // so if the lines has a lot product , we just update its product qty, by this method I have reduced 
            // its complexity to (O(n^2))
            _.each(self.env.pos.get_order().get_orderlines(), function (orderline) {
              var product_lots = self.env.pos.db.product_by_id_lot_no[orderline.product.id];
              if (product_lots) {
                _.each(product_lots, function (product_lot) {
                  var lot = self.env.pos.db.lot_no[product_lot];
                  if (lot && orderline.product.tracking == 'lot') 
                      lot.product_qty -= orderline.quantity;
                  else if (lot && orderline.product.tracking == 'serial')
                      lot.product_qty -= 1;
                });
              }
            });
          }
        }
  Registries.Component.extend(PaymentScreen, PosResPaymentScreen);
  return PaymentScreen;
});
