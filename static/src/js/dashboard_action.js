console.log('*********** Cargaré el archivo js')
odoo.define('smm_intecproof.dashboard_action', function (require){
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');
    var _t = core._t;
    var CustomDashBoard = AbstractAction.extend({
        events: {
            'click .medicamentos_vencidos': '_onClic_vencidos',
            'click .medicamentos_vencen_hoy': '_onClic_vencen_hoy',
        },

        template: 'CustomDashBoard',
        init: function(parent, context) {
           this._super(parent, context);
           this.dashboards_templates = ['DashboardProject'];
        },

        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.render_dashboards();
            });
        },

        _onClic_vencidos: function () {
            console.log('*********** Para ver si entra al botón vencidos' )
            var action = {
    			'name': 'Lotes expirados/vencidos',
	    		'type': 'ir.actions.act_window',
		    	'res_model': 'stock.lot',
			    'views': [[false, 'tree']],
                'target': 'current'
            };
            return this.do_action(action);
        },

        _onClic_vencen_hoy: function () {
            console.log('*********** Para ver si entra al botón vencen hoy' )

            return this.do_action({
                title: 'Send SMS Text Message',
                type: 'ir.actions.act_window',
                res_model: 'sms.composer',
                target: 'new',
                views: [[false, 'form']],
                context: context,
            });
        },

        willStart: function() {
            var self = this;
            return this._super()
            // return $.when(ajax.loadLibs(this), this._super()).then(function() {
            //    return self.fetch_data();
            //});
        },

        render_dashboards: function(){
            var self = this;
            this.fetch_data()
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_pj_dashboard').append(QWeb.render(template, {widget: self}));
            });
        },

        fetch_data: function() {
            var self = this;
            var def1 =  this._rpc({
                model: 'stock.lot',
                method: 'get_medicamentos_data'
            }).then(function(result){
                $('#medicamentos_vencidos').append('<span>' + result.total_medicamentos_vencidos + '</span>');
                $('#medicamentos_vencen_hoy').append('<span>' + result.total_medicamentos_hoy_vencen + '</span>');
                $('#medicamentos_proximos_a_vencer').append('<span>' + result.total_medicamentos_proximos_a_vencer + '</span>');
                $('#medicamentos_ok').append('<span>' + result.total_medicamentos_ok + '</span>');
            });
            return $.when(def1);
        },

        abrirVista() {
            console.log('*********** Para ver si entra al botón ');
            //var self = this;
            //self.ensure_one()
            return {
                'name': 'Prueba',
                'view_mode': 'tree',
                'res_model': 'stock.lot',
                'res_id': stock.view_production_lot_tree,
                'type': 'ir.actions.act_window',
                'context': {
                    'default_sale_line_id': self.id,
                },
                'target': 'new'
            }
        },

    });

    core.action_registry.add('custom_dashboard_tag', CustomDashBoard);

    return CustomDashBoard;

})

