from odoo import models, fields, api



class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    x_type = fields.Selection(related='picking_id.picking_type_code', string = 'tipo movimiento', store = True, readonly=True)

    
    @api.onchange('parent_location_id')
    def on_change_parent_location_id(self):
        for record in self:
            child=self.env['stock.location'].search([('location_id','=',record.parent_location_id.id),('x_stock_location', '=', True)])
            if child:
                record.original_location_id = child.id
                record.location_id = child.id
            else:
                record.original_location_id = False
                record.location_id = False
