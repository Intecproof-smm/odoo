# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (c) 2024-today Juan Carlos Flores.
#
#    This file is part of SMM_intecproof Module
#
#    This program is NOT a free software
#
###################################################################################
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class ExtendPosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    # ----------------------------------------------------------
    # Base de datos
    # ----------------------------------------------------------
    x_rubro = fields.Many2one(related='product_id.rubro', readonly=True, store=True, check_company=True)
