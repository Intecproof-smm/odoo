odoo.define('point_of_sale.WkLSAlertPopUp', function(require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');

    class WkLSAlertPopUp extends AbstractAwaitablePopup {
        getPayload() {
            return null;
        }
    }
    WkLSAlertPopUp.template = 'WkLSAlertPopUp';
    WkLSAlertPopUp.defaultProps = {
        title: 'Confirm ?',
        body: '',
    };
    Registries.Component.add(WkLSAlertPopUp);
    return WkLSAlertPopUp;
});