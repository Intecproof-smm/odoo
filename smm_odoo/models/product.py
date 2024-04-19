from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    allow_negative_stock = fields.Boolean(
        string="Permitir Existencias en Negativo"
    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    allow_negative_stock = fields.Boolean(
        string="Permitir Existencias en Negativo"
    )
    

    is_controlled_product = fields.Boolean(
        string="Es producto controlado",
        default = False
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    location_org = fields.Many2one('stock.location', 'Source Location')
    location_des = fields.Many2one('stock.location', 'Destination Location')
