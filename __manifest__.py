# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (c) 2023-today Juan Carlos Flores.
#
#    This file is part of SMM_intecproof Module
#
#    This program is NOT a free software
#
###################################################################################
{
    "name": "SMM-Intecproof",
    "author": "Juan Carlos Flores",
    "support": "jcflores@intecproof.com",
    "category": "Extra Tools",
    "license": "OPL-1",
    "summary": "Agrega funcionalidades extras al módulo de Inventarios para el proyecto SMMG DOS",
    "description": """Este módulo agrega diferentes funcionalidades a Odoo para cumplir con el proyecto de SMMG""",
    "version": "1.2.1",
    "sequence": 1,
    "depends": ["base", "stock", "pos_sale", "sale", "contacts", 'point_of_sale', "smm_odoo"],
    "application": True,
    "auto_install": False,
    "installable": True,
    "images": ["static/description/icon.png", ],
    "data": [
        "views/productos.xml",
        "views/contactos.xml",
        "views/server_actions.xml",
        "views/dashboard_menu.xml",
        "views/report_pos_orders.xml",
        "views/report_historicos.xml",
        "views/pos_order_list_tree.xml",
        'views/pos_dialogbox.xml',
        "views/eventos_medicos.xml",
        "views/purchase_report.xml",
        'views/servicios.xml',
        "data/eventos_medicos.xml",
        "report/report_historicos_template.xml",
        "report/report_conteos_firmas_template.xml",
        "report/purchase_order_report.xml",
        "security/ir.model.access.csv",
        "views/pos_payment_method.xml"
    ],
    'assets': {
        'web.assets_backend': [
            'smm_intecproof/static/src/js/dashboard_action.js',
            'smm_intecproof/static/src/xml/dashboard.xml',
            'smm_intecproof/static/src/js/notificaciones.js',
            'smm_intecproof/static/src/js/servicio_notificaciones.js',
            'smm_intecproof/static/src/js/purchase_report.js',
            'smm_intecproof/static/src/css/purchase_report.css',
            'smm_intecproof/static/src/xml/purchase_report_view.xml'
        ],
        'web.assets_common': [
        ],
        'point_of_sale.assets': [
            'smm_intecproof/static/src/js/NewActionpadWidget.js',
            'smm_intecproof/static/src/xml/NewActionpadWidget.xml',
            'smm_intecproof/static/src/js/DatosSalidaPopup.js',
            'smm_intecproof/static/src/xml/DatosSalidaPopup.xml',
            'smm_intecproof/static/src/js/models.js',
            # 'smm_intecproof/static/src/xml/SolicitanteButton.xml',
            # 'smm_intecproof/static/src/js/SolicitanteButton.js',
            'smm_intecproof/static/src/js/ExtendedProductScreen.js',
            'smm_intecproof/static/src/css/pos.css',
            "smm_intecproof/static/src/js/payment_terminal.js",
            "smm_intecproof/static/src/xml/OrderReceipt.xml",
            "smm_intecproof/static/src/xml/PaymentScreen.xml",
            "smm_intecproof/static/src/xml/Chrome.xml"
        ],
    },
}
