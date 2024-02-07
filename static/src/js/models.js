console.log("Entrando a smm_pos.models.js");
odoo.define("smm_pos.models", function(require) {
    "use strict";

    const { Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    const SmmOrder = (Order) =>
        class extends Order {
            constructor() {
                super(...arguments);
                this.x_area_solicitud = this.x_area_solicitud || null;
                this.x_cama = this.x_cama || null;
                this.x_fecha_nacimiento = this.x_fecha_nacimiento || null;
                this.x_no_ambulancia = this.x_no_ambulancia || null;
                this.x_solicitante = this.x_solicitante || null;
                this.x_turno = this.x_turno || null;
                this.x_expediente = this.x_expediente || null;
                this.x_diagnostico = this.x_diagnostico || null;
                this.x_dosis_aplicada = this.x_dosis_aplicada || null;
                this.x_via_aplicacion = this.x_via_aplicacion || null;
                this.x_indicacion = this.x_indicacion || null;
            }

            save_datos_adicionales(area_solicitud, cama, no_ambulancia, turno, expediente, diagnostico, dosis_aplicada, via_aplicacion, indicacion) {
                this.x_area_solicitud = area_solicitud || null;
                this.x_cama = cama || null;
                this.x_no_ambulancia = no_ambulancia || null;
                this.x_turno = turno || null;
                this.x_expediente = expediente || null;
                this.x_diagnostico = diagnostico || null;
                this.x_dosis_aplicada = dosis_aplicada || null;
                this.x_via_aplicacion = via_aplicacion || null;
                this.x_indicacion = indicacion || null;
            }

            export_as_JSON() {
                var data = super.export_as_JSON.apply(this, arguments);
                data.x_area_solicitud = this.x_area_solicitud;
                data.x_cama = this.x_cama;
                data.x_fecha_nacimiento = this.x_fecha_nacimiento;
                data.x_no_ambulancia = this.x_no_ambulancia;
                data.x_solicitante = this.x_solicitante;
                data.x_turno = this.x_turno;
                data.x_expediente = this.x_expediente;
                data.x_diagnostico = this.x_diagnostico;
                data.x_dosis_aplicada = this.x_dosis_aplicada;
                data.x_via_aplicacion = this.x_via_aplicacion;
                data.x_indicacion = this.x_indicacion;
                return data;
            }

            init_from_JSON(json) {
                this.x_area_solicitud = json.x_area_solicitud;
                this.x_cama = json.x_cama;
                this.x_fecha_nacimiento = json.x_fecha_nacimiento;
                this.x_no_ambulancia = json.x_no_ambulancia;
                this.x_solicitante = json.x_solicitante;
                this.x_turno = json.x_turno;
                this.x_expediente = json.x_expediente;
                this.x_diagnostico = json.x_diagnostico;
                this.x_dosis_aplicada = json.x_dosis_aplicada;
                this.x_via_aplicacion = json.x_via_aplicacion;
                this.x_indicacion = json.x_indicacion;
                super.init_from_JSON.call(this, json);
            }

            get_solicitante() {
                return this.x_solicitante;
            }
        
            set_solicitante(solicitante) {
                this.assert_editable();
                this.x_solicitante = solicitante;
            }
    }

    Registries.Model.extend(Order, SmmOrder);
    return SmmOrder;
});