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
        }

        setup() {
            super.setup();
            this.state = useState(
                { 
                    ds_cama: this.props.ds_cama
                    , ds_no_ambulancia: this.props.ds_no_ambulancia
                    , ds_area: this.props.ds_area 
                    , ds_expediente: this.props.ds_expediente
                    , ds_diagnostico: this.props.ds_diagnostico
                    , ds_dosis: this.props.ds_dosis
                    , ds_via: this.props.ds_via
                    , ds_indicacion: this.props.ds_indicacion
                    , ds_receta: this.props.ds_receta
                    , ds_medico: this.props.ds_medico
                    , isInvalid: false
                    , es_controlado: this.props.es_controlado
                });
            console.log("DatosSalidaPopup.setup()")
        }

        getPayload() {
            return this.state;
        }

        async confirm() {
            if(!this.state.ds_cama || !this.state.ds_no_ambulancia || !this.state.ds_area 
                || (this.state.es_controlado && (!this.state.ds_receta || !this.state.ds_indicacion || !this.state.ds_medico))) {
                this.state.isInvalid = true;
            } else {
                this.state.isInvalid = false;
                super.confirm();
            }
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