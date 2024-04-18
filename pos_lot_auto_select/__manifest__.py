# -*- coding: utf-8 -*-

{
    'name': 'POS Lot Auto Selection depend on expiry date',
    'version': '16.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Ahmed Elmahdi',
    'summary': 'Using this module to auto select LOT/Serial in POS sorted by expiry date',
    'description': """
    Using this module to auto select LOT/Serial in POS sorted by expiry date
""",
    'depends': ['point_of_sale','product_expiry'],
    'data': [
        'views/pos.xml',
    ],

    'assets': {
        'point_of_sale.assets': [
            'pos_lot_auto_select/static/src/js/models.js',
            'pos_lot_auto_select/static/src/js/PaymentScreen.js',
            'pos_lot_auto_select/static/src/js/EditListPopup.js',
            'pos_lot_auto_select/static/src/js/OrderWidget.js',
            'pos_lot_auto_select/static/src/js/ProductScreen.js',
            'pos_lot_auto_select/static/src/xml/pos.xml',

        ],
        # 'web.assets_qweb': [
        # ],
    },

    "images": ["static/description/image.png", ],
    'license': 'LGPL-3',

    'installable': True,
    'auto_install': False,
    'price': 87,
    'currency': 'EUR',
    'live_test_url':'https://youtu.be/Yt9_H06ANvU',

}
