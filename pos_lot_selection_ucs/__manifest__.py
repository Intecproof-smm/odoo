# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO Open Source Management Solution
#
#    ODOO Addon module by Uncanny Consulting Services LLP
#    Copyright (C) 2022 Uncanny Consulting Services LLP (<https://uncannycs.com>).
#
##############################################################################
{
    "name": "POS LOT Selection",
    "version": "16.0.1.0.0",
    "summary": """Select lots and choose qty from multiple lots, show expiry date""",
    "description": """Select lots and choose qty from multiple lots, show expiry date""",
    "license": "Other proprietary",
    "author": "Uncanny Consulting Services LLP",
    "maintainers": "Uncanny Consulting Services LLP",
    "website": "https://uncannycs.com",
    "category": "Sales/Point of Sale",
    "depends": ["point_of_sale", "product_expiry"],
    "data": [
        "views/pos_config_views.xml",
    ],
    "assets": {
        "point_of_sale.assets": [
            "pos_lot_selection_ucs/static/src/js/models.js",
            "pos_lot_selection_ucs/static/src/js/EditListPopup.js",
            "pos_lot_selection_ucs/static/src/js/ProductScreen.js",
            "pos_lot_selection_ucs/static/src/js/Orderline.js",
            "pos_lot_selection_ucs/static/src/xml/EditListPopup.xml",
        ],
    },
    "images": ["static/description/banner.gif"],
    "installable": True,
    "application": True,
    "auto_install": False,
    "price": 30,
    "currency": "USD",
}
