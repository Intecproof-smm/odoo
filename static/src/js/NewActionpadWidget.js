console.log("Cargando NewActionpadWidget.js");
odoo.define('smm_pos.NewActionPadWidget', function(require) {
    'use strict';
    
    const Registries = require('point_of_sale.Registries');
    const ActionpadWidget = require('point_of_sale.ActionpadWidget');
    const { Gui } = require('point_of_sale.Gui');
    const { useListener } = require("@web/core/utils/hooks");
    
    // *: Sobreescribimos algunas funciones del Widget
    const WidgetsOverride = (ActionpadWidget) =>
        class extends ActionpadWidget {
            setup() {
                super.setup();
                useListener('click-pago', this.onClickPago);
            }

            async onClickPago()  {
                var self = this;
                var continuar = true;
                console.log("Entrando a onClickPago()");

                // Verificamos que el paciente esté capturado
                if (!this.currentOrder().partner) {
                    this.showPopup("ErrorPopup", {
                        title: "Acción No Válida",
                        body: "No se ha capturado el paciente.",
                    });
                    continuar = false;
                }
                
                if (continuar) {
                    // Desplegamos el pop-up que va a capturar los datos para dar salida
                    // del inventario
                    // *: las variables en las que se almacena el resultado se deben llamar 
                    // "confirmed" y "payload" para que funcione. Si no, regresa undefined.
                    const ordenConControlados = this.esOrdenConControlados();
                    console.log("Tiene controlados:" + ordenConControlados);
                    const { confirmed, payload } = await this.showPopup("DatosSalidaPopup", {es_controlado: ordenConControlados});
                    console.log("Finalizado desplegado de ventana con valor:" + confirmed);
                    
                    if (confirmed) {
                        if (this.currentOrder().orderlines.some(line => line.get_product().tracking !== 'none' && !line.has_valid_product_lot()) && (this.env.pos.picking_type.use_create_lots || this.env.pos.picking_type.use_existing_lots)) {
                            const { confirmed } = await this.showPopup('ConfirmPopup', {
                            title: this.env._t('Some Serial/Lot Numbers are missing'),
                            body: this.env._t('You are trying to sell products with serial/lot numbers, but some of them are not set.\nWould you like to proceed anyway?'),
                            confirmText: this.env._t('Yes'),
                            cancelText: this.env._t('No')
                        });
                        if (confirmed) {
                            this.fillData(payload);
                            Gui.showScreen('PaymentScreen');
                        }
                    } else {
                        this.fillData(payload);
                        Gui.showScreen('PaymentScreen');
                    }
                }
            }

                console.log("Finalizando onClickPago()");
            }

            fillData(payload) {
                this.currentOrder().save_datos_adicionales(payload.ds_area
                    , payload.ds_cama
                    , payload.ds_no_ambulancia
                    , this.env.pos.pos_session.x_turno
                    , payload.ds_expediente
                    , payload.ds_diagnostico
                    , payload.ds_dosis_aplicada
                    , payload.ds_via_aplicacion
                    , payload.ds_indicacion
                );
            }

            currentOrder() {
                return this.env.pos.get_order();
            }

            esOrdenConControlados() {
                return this.currentOrder().orderlines.some((line) => line.product.is_controlled_product);
            }
    };

    Registries.Component.extend(ActionpadWidget, WidgetsOverride);
    return ActionpadWidget;
});