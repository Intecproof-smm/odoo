from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools import config, float_compare


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.constrains("product_id", "quantity")
    def check_negative_qty(self):
        p = self.env["decimal.precision"].precision_get("Product Unit of Measure")

        for quant in self:
            disallowed_by_product = (
                not quant.product_id.allow_negative_stock
                and not quant.product_id.categ_id.allow_negative_stock
            )
            disallowed_by_location = not quant.location_id.allow_negative_stock

            movimiento_entrada = False
            if (quant.product_id.location_org == quant.product_id.location_des):
                movimiento_entrada = True

            if (
                (float_compare(quant.quantity, 0, precision_digits=p) == -1
                    or float_compare(quant.available_quantity, 0, precision_digits=p) == -1
                )
                and quant.product_id.type == "product"
                and quant.location_id.usage in ["internal", "transit"]
                and disallowed_by_product
                and disallowed_by_location
                and not movimiento_entrada
            ):
                msg_add = ""
                if quant.lot_id:
                    msg_add = _(" lot '%s'") % quant.lot_id.name_get()[0][1]
                raise ValidationError(
                    _(
                        "Error de validacion de esta operacion por que "
                        "la existencia del producto '%s'%s se volveria a negativo "
                        "(%s) en la ubicacion de existencias '%s' por lo tanto no esta permitido."
                    )
                    % (
                        quant.product_id.display_name,
                        msg_add,
                        quant.quantity,
                        quant.location_id.complete_name,
                    )
                )
