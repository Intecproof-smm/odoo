from odoo import models, fields, api, _
from dateutil import relativedelta
import dateutil
from datetime import datetime
import logging


months = [
    ('1', 'Enero')
    , ('2', 'Febrero')
    , ('3', 'Marzo')
    , ('4', 'Abril')
    , ('5', 'Mayo')
    , ('6', 'Junio')
    , ('7', 'Julio')
    , ('8', 'Agosto')
    , ('9', 'Septiembre')
    , ('10', 'Octubre')
    , ('11', 'Noviembre')
    , ('12', 'Diciembre')
]

_logger = logging.getLogger(__name__)


class PurchaseOrderBudget(models.Model):
    _name = 'purchase.order.budget'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string = 'Nombre del presupuesto',
        readonly = True,
        compute = '_compute_budget_name',
        tracking = True,
        store = True,
    )
    picking_type_id = fields.Many2one(
        comodel_name = 'stock.picking.type',
        string = 'Tipo de operación',
        required = True,
        default = False,
        tracking = True,
        domain = "[('code','=','incoming')]"
    )
    picking_type_complete_name = fields.Char(related = 'picking_type_id.name', readonly = True, store = True)
    category = fields.Many2one(
        comodel_name = 'product.category',
        string = "Categoría",
        tracking = True,
        required = True
    )
    initial_month = fields.Selection(
        months,
        required = True,
        default = str(fields.date.today().month),
        tracking = True,
        string = "Mes"
    )
    initial_year = fields.Integer(
        required = True,
        default = fields.date.today().year,
        tracking = True,
        string = "Año"
    )
    initial_date = fields.Date(
        string = "Fecha inicial",
        readonly = True,
        store = True,
        compute = '_compute_initial_date'
    )
    final_month = fields.Selection(
        months,
        required = True,
        default = str(fields.date.today().month),
        tracking = True,
        string = "Mes"
    )
    final_year = fields.Integer(
        required = True,
        default = fields.date.today().year,
        tracking = True,
        string = "Año"
    )
    final_date = fields.Date(string = "Fecha final", readonly = True, compute = '_compute_final_date', store = True)
    line_ids = fields.One2many('purchase.order.budget.line', 'purchase_order_budget_id', 'Líneas', auto_join = True)

    @api.depends('picking_type_id', 'category', 'initial_date', 'final_date')
    def _compute_budget_name(self):
        self.name = 'Sin datos completos'

        if self.picking_type_complete_name and self.category:
            self.name = "%s - %s, %s - %s" % (
                self.picking_type_complete_name or '', self.category.name or '', self.initial_date, self.final_date
            )

    @api.depends('initial_month', 'initial_year')
    def _compute_initial_date(self):
        if self.initial_month and self.initial_year:
            for rec in self:
                rec.initial_date = datetime.strptime(
                    "1/" + str(rec.initial_month) + "/" + str(rec.initial_year), "%d/%m/%Y"
                )

    @api.depends('final_month', 'final_year')
    def _compute_final_date(self):
        if self.final_month and self.final_year:
            for rec in self:
                fecha_temporal = datetime.strptime("1/" + str(rec.final_month) + "/" + str(rec.final_year), "%d/%m/%Y")
                self.final_date =\
                    fecha_temporal + dateutil.relativedelta.relativedelta(
                        months = 1
                    ) + dateutil.relativedelta.relativedelta(days = -1)
