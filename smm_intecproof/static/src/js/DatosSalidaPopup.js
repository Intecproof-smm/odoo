console.log("Cargando DatosSalidaPopup.js");
odoo.define('smm_pos.DatosSalidaPopup', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');
    const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');

    const { useState } = owl;

    class DatosSalidaPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState(
                { 
                    c_cama: this.props.ds_cama
                    , c_ambulancia: this.props.ds_no_ambulancia
                    , c_turno: this.props.ds_turno
                    , c_area: this.props.ds_area 
                    , c_expediente: this.props.ds_expediente
                    , c_diagnostico: this.props.ds_diagnostico
                    , c_dosis: this.props.ds_dosis
                    , c_via: this.props.ds_via
                    , c_indicacion: this.props.ds_indicacion
                });
        }

        setup() {
            super.setup();
            console.log("DatosSalidaPopup.setup()")
        }

        getPayload() {
            return this.state;
        }
    }

    DatosSalidaPopup.template = 'DatosSalidaPopup';
    DatosSalidaPopup.defaultProps = {
        confirmText: "De Acuerdo"
        , cancelText: "Cancelar"
        , title: "Datos de salida"
        , confirmKey: "Enter"
        , cancelKey: "Escape"
        , body: ""
        , es_controlado: "false"
    };
    Registries.Component.add(DatosSalidaPopup);
    console.log("Finalizando DatosSalidaPopup.js");
    return DatosSalidaPopup;
})