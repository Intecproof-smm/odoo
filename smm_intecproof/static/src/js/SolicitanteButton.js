odoo.define('smm_pos.SolicitanteButton', function (require) {
    'use strict';

    const { Gui } = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const { identifyError } = require('point_of_sale.utils');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');

    class SolicitanteButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }

        get isLongName() {
            return this.solicitante && this.solicitante.name.length > 10;
        }

        get currentOrder() {
            return this.env.pos.get_order();
        }

        get solicitante() {
            return this.currentOrder ? this.currentOrder.get_solicitante() : null;
        }

        async onClick() {
            // IMPROVEMENT: This code snippet is very similar to selectPartner of PaymentScreen.
            const currentSolicitante = this.solicitante;
            const { confirmed, payload: newSolicitante } = await this.showTempScreen(
                'PartnerListScreen',
                { partner: currentSolicitante }
            );
            if (confirmed) {
                this.currentOrder.set_solicitante(newSolicitante);
            }
        }
    }

    SolicitanteButton.template = 'SolicitanteButton';
    ProductScreen.addControlButton({
        component: SolicitanteButton,
        condition: function() {
            return true;
        },
    });

    Registries.Component.add(SolicitanteButton);
    return SolicitanteButton;
 });