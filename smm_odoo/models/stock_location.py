from odoo import models, fields,api


class StockLocation(models.Model):
    _inherit = 'stock.location'

    x_branch = fields.Many2one('res.branch', string = 'Almacen', store = True)
    x_stock_location = fields.Boolean(string='¿Es ubicación de existencias?', store=True)
    x_branches = fields.Many2many('res.branch', string='Almacenes permitidos',
                                        relation='x_res_branch_stock_picking_rel',column1="stock_picking_id", column2="res_branch_id", 
                                        store=False, readonly=True, 
                                        compute= '_compute_branches')


    @api.depends("x_branches")
    def _compute_branches(self):
        for record in self:
            record['x_branches'] = self.env.user.branch_ids


    allow_negative_stock = fields.Boolean(
        string="Permitir Existencias en Negativo",
        help="Permitir existencia en negativo en esta ubicacion",
    )