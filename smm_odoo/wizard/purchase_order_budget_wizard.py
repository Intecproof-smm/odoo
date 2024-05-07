from odoo import models, fields, api, _
from dateutil import relativedelta
import dateutil
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

months = [
    ('1', 'Enero'),
    ('2', 'Febrero'),
    ('3', 'Marzo'),
    ('4', 'Abril'),
    ('5', 'Mayo'),
    ('6', 'Junio'),
    ('7', 'Julio'),
    ('8', 'Agosto'),
    ('9', 'Septiembre'),
    ('10', 'Octubre'),
    ('11', 'Noviembre'),
    ('12', 'Diciembre'),
]


class PurchaseOrderBudgetWizard(models.TransientModel):
    _name = 'purchase.order.budget.wizard'

    @api.model
    def _generar_presupuesto(self):
        # Traer el contexto para obtener los valores de los datos
        ctx = dict(self.env.context or {})

        domain = [
            ('order_id.date_order', '>=', ctx['initial_date']),
            ('order_id.date_order', '<=', ctx['final_date']),
            ('product_id.categ_id.complete_name', '=', ctx['category_name']),
            ('order_id.state', 'in', ['done', 'purchase']),
            ('order_id.picking_type_id', '=', ctx['picking_type_id'])
        ]

        initial_date = datetime.strptime(ctx['initial_date'], "%Y-%m-%d")
        initial_month = initial_date.month
        initial_year = initial_date.year
        final_date = datetime.strptime(ctx['final_date'], "%Y-%m-%d")
        final_month = final_date.month
        final_year = final_date.year

        campos = ['product_id', 'product_qty:sum', 'product_id.id', 'price_unit', 'price_subtotal:sum']
        agrupador = ['product_id']
        orden = 'product_id'

        purchase_order_budget = self.env['purchase.order.budget'].create(
            {
                'name':         "Se calculará automáticamente",
                'picking_type_id': ctx['picking_type_id'],
                'category':    ctx['category_id'],
                'initial_month':  str(initial_month),
                'initial_year':  str(initial_year),
                'final_month':    str(final_month),
                'final_year':    str(final_year),
            }
        )

        purchase_order_lines = self.env['purchase.order.line'].read_group(
            domain = domain,
            fields = campos,
            groupby = agrupador,
            orderby = orden,
            offset = 0,
            limit = None,
            lazy = False
        )

        for line in purchase_order_lines:
            self.env['purchase.order.budget.line'].create(
                {
                    'purchase_order_budget_id': purchase_order_budget.id,
                    'product_id':               str(line['product_id'][0]),
                    'quantity':                 line['product_qty'],
                    'price_unit':               line['price_subtotal']/line['product_qty'],
                    'price_subtotal':           line['price_subtotal']
                }
            )

    picking_type_id = fields.Many2one(
        comodel_name = 'stock.picking.type',
        string = 'Tipo de operación',
        required = True,
        default = False,
        tracking = True,
        domain = "[('code','=','incoming')]"
    )
    category_id = fields.Many2one(
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

    # consulta_line_ids = fields.Many2one(
    #     comodel_name = 'stock.move.line',
    #     string = 'Detalle'
    # )

    @api.depends('initial_month', 'initial_year')
    def _compute_initial_date(self):
        if self.initial_month and self.initial_year:
            for rec in self:
                rec.initial_date = datetime.strptime(
                    "1/" + str(rec.initial_month) + "/" + str(rec.initial_year),
                    "%d/%m/%Y"
                    )

    @api.depends('final_month', 'final_year')
    def _compute_final_date(self):
        fecha_temporal = datetime.strptime("1/" + str(self.final_month) + "/" + str(self.final_year), "%d/%m/%Y")
        self.final_date =\
            fecha_temporal + dateutil.relativedelta.relativedelta(months = 1) + dateutil.relativedelta.relativedelta(
                days = -1
            )

    def traer_datos_consulta(self):
        stock_picking_type = self.env['stock.picking.type'].search(
            [('name', '=', 'Recepciones'), ('warehouse_id.name', '=', 'SMM-General')], limit = 1
        )
        # Cambiar las fechas de Date a Datetime para poder hacer el filtro de manera completa
        fecha_ini = datetime(self.initial_date.year, self.initial_date.month, self.initial_date.day)
        fecha_fin = datetime(self.final_date.year, self.final_date.month, self.final_date.day)

        domain = [
            ('order_id.date_order', '>=', fecha_ini),
            ('order_id.date_order', '<=', fecha_fin),
            ('product_id.categ_id.complete_name', '=', self.category_id.complete_name),
            ('order_id.state', 'in', ['done', 'purchase']),
            ('order_id.picking_type_id', '=', stock_picking_type.id)
        ]

        # Traer el contexto para actualizar los agrupadores
        ctx = dict(self.env.context or {})
        ctx['inventory_report_mode'] = True
        ctx['group_by'] = ['product_id', 'create_date:month']
        ctx['initial_date'] = self.initial_date
        ctx['final_date'] = self.final_date
        ctx['consulta_presupuesto'] = True
        ctx['category_id'] = self.category_id.id
        ctx['category_name'] = self.category_id.complete_name
        ctx['picking_type_id'] = self.picking_type_id.id

        # Obtener el identificador de la vista de lista que necesito para mostrar el resultado
        tree_view_id = self.env.ref('smm_odoo.view_purchase_order_line_tree_budget').id
        # Mandar llamar la list del modelo stock_move_line ya existente
        return {
            'type':      'ir.actions.act_window',
            'views':     [(tree_view_id, 'tree')],
            'view_mode': 'tree',
            'context':   ctx,
            'name':      _(
                'Consulta de ' + self.category_id.name + ' en ' + self.picking_type_id.name + ' del ' +
                str(self.initial_date) + ' al ' + str(self.final_date)
            ),
            'res_model': 'purchase.order.line',
            'domain':    domain,
        }
