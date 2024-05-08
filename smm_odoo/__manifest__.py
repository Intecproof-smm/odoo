{
    'name': 'smm_odoo'
    , 'version': "16.0.1.0.1"
    , 'description': 'Modulo de personalizacion de Servicios Medicos Municipales'
    , 'author': 'smm'
    , 'depends': [
        'base'
        , 'contacts'
        , 'stock'
        , 'stock_account'
        , 'multi_branch_base'
    ]
    , 'data': [
        'security/ir.model.access.csv'
        , 'views/res_users_views.xml'
        , 'views/stock_move_line_view.xml'
        , 'views/stock_picking_views.xml'
        , 'views/stock_scrap_view.xml'
        , 'views/stock_warehouse_views.xml'
        , 'views/stock_location_views.xml'
        , 'views/stock_return_picking_view.xml'
        , 'wizard/stock_picking_button_validate_wizard.xml'
        , 'security/ir_rule_stock_ping.xml'
        , 'views/product_product_views.xml'
        , 'reports/reports.xml'
        , 'reports/smm_reporte_entrega.xml'
        , 'reports/smm_reporte_entrega_ubicaciones.xml'
    ]
    , 'application': False
    , 'auto_install': False
}
