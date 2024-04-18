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

from odoo import api, models
import datetime
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.AbstractModel):
    _name = 'report.smm_intecproof.purchase_order_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        if self.env.context.get('purchase_order_report'):
            if data.get('report_data'):
                data.update({'report_main_line_data': data.get('report_data')['report_lines'],
                             'Filters': data.get('report_data')['filters'],
                             'company': self.env.company,
                             'desde': datetime.datetime.strptime(data.get('report_data')['orders']['date_from'],
                                                                 '%Y-%m-%d %H:%M:%S').date(),
                             'hasta': datetime.datetime.strptime(data.get('report_data')['orders']['date_to'],
                                                                 '%Y-%m-%d %H:%M:%S').date(),
                             })
                _logger.info('El filtro es: %s ', data.get('report_data'))
                _logger.info('Desde: %s hasta: %s ', str(data.get('report_data')['orders']['date_from']),
                             str(data.get('report_data')['orders']['date_to']))
            return data
