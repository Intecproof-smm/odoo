from odoo import models, fields, api
from dateutil import relativedelta
import dateutil
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrderBudgetLine(models.Model):
    _name = 'purchase.order.budget.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    purchase_order_budget_id = fields.Many2one(
        comodel_name = 'purchase.order.budget',
        autojoin = True,
        string = 'Presupuesto'
    )
    product_id = fields.Many2one(
        comodel_name = 'product.product',
        string = 'Producto',
        required = True,
        tracking = True
    )
    quantity = fields.Float(default = '0', required = True, tracking = True)
    price_unit = fields.Float(default = '0', required = True, tracking = True)
    price_subtotal = fields.Float(default = '0', required = True, tracking = True)

    quantity_consumed_period = fields.Float(
        compute = '_compute_quantity_consumed_period',
        store = False,
        string = 'Periodo actual'
    )
    quantity_consumed_previous_period = fields.Float(
        compute = '_compute_quantity_consumed_previous_period',
        store = False,
        string = 'Periodo anterior'
    )
    quantity_consumed_last_year = fields.Float(
        compute = '_compute_quantity_consumed_last_year',
        store = False,
        string = 'Año anterior'
    )

    @api.model
    def _compute_quantity_consumed_period(self):
        stock_picking_type = self.env['stock.picking.type'].search(
            [('name', '=', 'Recepciones'), ('warehouse_id.name', '=', 'SMM-General')], limit = 1
        )

        for rec in self:
            domain = [
                ('order_id.date_order', '>=', rec.purchase_order_budget_id.initial_date),
                ('order_id.date_order', '<=', rec.purchase_order_budget_id.final_date),
                ('product_id.categ_id.complete_name', '=', rec.purchase_order_budget_id.category.complete_name),
                ('product_id', '=', rec.product_id.id),
                ('order_id.state', 'in', ['done', 'purchase']),
                ('order_id.picking_type_id', '=', stock_picking_type.id),
            ]
            quantity = 0
            purchase_order_lines = self.env['purchase.order.line'].search(domain)

            for line in purchase_order_lines:
                quantity += line.product_qty
            rec.quantity_consumed_period = quantity

    @api.model
    def _compute_quantity_consumed_previous_period(self):
        for rec in self:
            if rec.purchase_order_budget_id.initial_month and rec.purchase_order_budget_id.final_month and\
                rec.purchase_order_budget_id.initial_year and rec.purchase_order_budget_id.final_year:
                # Calcular el lapso de tiempo que hay entre las 2 fechas en meses y años
                lapso_meses = (int(rec.purchase_order_budget_id.final_month) - int(rec.purchase_order_budget_id.initial_month)) + 1
                lapso_anos = rec.purchase_order_budget_id.final_year - rec.purchase_order_budget_id.initial_year
                # Validar que los lapsos no sean negativos.
                if lapso_meses < 0 or lapso_anos < 0:
                    rec.quantity_consumed_previous_period = 0
                    return
                # Calcular la fecha inicial del periodo anterior
                if int(rec.purchase_order_budget_id.initial_month) <= lapso_meses:
                    lm = lapso_meses - (int(rec.purchase_order_budget_id.initial_month) - 1)
                    initial_month = 13 - lm
                    initial_year = rec.purchase_order_budget_id.initial_year - (lapso_anos + 1)
                else:
                    initial_month = int(rec.purchase_order_budget_id.initial_month) - lapso_meses
                    initial_year = int(rec.purchase_order_budget_id.initial_year) - lapso_anos
                fecha_inicial = datetime(initial_year, initial_month, 1)
                # Calcular la fecha final del periodo anterior
                if int(rec.purchase_order_budget_id.final_month) <= lapso_meses:
                    lm = lapso_meses - (int(rec.purchase_order_budget_id.final_month) - 1)
                    final_month = 13 - lm
                    final_year = rec.purchase_order_budget_id.final_year - (lapso_anos + 1)
                else:
                    final_month = int(rec.purchase_order_budget_id.final_month) - lapso_meses
                    final_year = int(rec.purchase_order_budget_id.final_year) - lapso_anos
                fecha_temporal = datetime(final_year, final_month, 1)
                fecha_final = fecha_temporal +\
                              dateutil.relativedelta.relativedelta(months = 1) + dateutil.relativedelta.relativedelta(
                    days = -1
                )
                # Traer la ubicación del almacén General
                ubicacion = self.env['stock.location'].search([('complete_name', '=', 'SMM-G/Existencias')], limit = 1)
                # Traer los datos de la partida para regresar el consumo
                _logger.info(str(fecha_inicial))
                _logger.info(str(fecha_final))

                domain = [
                    ('order_id.date_order', '>=', fecha_inicial),
                    ('order_id.date_order', '<=', fecha_final),
                    ('product_id.categ_id.complete_name', '=', rec.purchase_order_budget_id.category.complete_name),
                    ('product_id', '=', rec.product_id.id),
                    ('order_id.state', 'in', ['done', 'purchase']),
                    ('order_id.picking_type_id', '=', rec.purchase_order_budget_id.picking_type_id.id)
                ]
                cantidad = 0
                purchase_order_lines = self.env['purchase.order.line'].search(domain)
                for line in purchase_order_lines:
                    cantidad += line.product_qty
                rec.quantity_consumed_previous_period = cantidad
            else:
                rec.quantity_consumed_previous_period = 0

    @api.model
    def _compute_quantity_consumed_last_year(self):
        # Calcular la fecha incial del año anterior
        for rec in self:
            if rec.purchase_order_budget_id.initial_month and rec.purchase_order_budget_id.final_month and\
                rec.purchase_order_budget_id.initial_year and rec.purchase_order_budget_id.final_year:
                # Calcular la fecha inicial y final de un año antes
                fecha_inicial = datetime(rec.purchase_order_budget_id.initial_year - 1, int(rec.purchase_order_budget_id.initial_month), 1)
                fecha_temporal = datetime(rec.purchase_order_budget_id.final_year - 1, int(rec.purchase_order_budget_id.final_month), 1)
                fecha_final = fecha_temporal +\
                              dateutil.relativedelta.relativedelta(months = 1) + dateutil.relativedelta.relativedelta(
                    days = -1
                )
                # Traer la ubicación del almacén General
                ubicacion = self.env['stock.location'].search([('complete_name', '=', 'SMM-G/Existencias')], limit = 1)
                # Traer los datos de la partida para regresar el consumo

                domain = [
                    ('order_id.date_order', '>=', fecha_inicial),
                    ('order_id.date_order', '<=', fecha_final),
                    ('product_id.categ_id.complete_name', '=', rec.purchase_order_budget_id.category.complete_name),
                    ('product_id', '=', rec.product_id.id),
                    ('order_id.state', 'in', ['done', 'purchase']),
                    ('order_id.picking_type_id', '=', rec.purchase_order_budget_id.picking_type_id.id)
                ]
                cantidad = 0
                purchase_order_lines = self.env['purchase.order.line'].search(domain)
                for line in purchase_order_lines:
                    cantidad += line.product_qty
                rec.quantity_consumed_last_year = cantidad
            else:
                rec.quantity_consumed_last_year = 0
