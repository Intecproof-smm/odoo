console.log("Cargando ExtendedProductScreen.js");
odoo.define('smm_pos.ExtendedProductScreen', function(require) {
    'use strict';

    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require("point_of_sale.ProductScreen");

    const ExtendProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _clickProduct(event) {
                var addProduct = true;
                var errorMessage = null;

                if (!this.currentOrder) {
                    this.env.pos.add_new_order();
                }
                else {
                    const product = event.detail;
                    if(product.is_controlled_product) {
                        if(this.currentOrder.orderlines.length != 0) {
                            errorMessage = "Solamente puede existir un medicamento controlado en la orden."
                            addProduct = false;
                        }
                    }
                    else {
                        this.currentOrder.orderlines.forEach(line => {
                            if(line.product.is_controlled_product) {
                                errorMessage = "Los medicamentos controlados no se pueden agregar en una orden que tiene medicamentos no controlados."
                                addProduct = false;
                            }
                        });
                    }
                }
                
                if(addProduct)
                    super._clickProduct(event);
                else
                    this.showPopup("ErrorPopup", {
                        title: "Acción No Válida",
                        body: errorMessage,
                    });

            }
        };

    Registries.Component.extend(ProductScreen, ExtendProductScreen);
    return ProductScreen;
});
