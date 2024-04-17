# Copyrght 2020 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    def _get_payment_terminal_selection(self):
        res = super()._get_payment_terminal_selection()
        res.append(("vevent_payment_terminal", _("Vevent Payment Terminal")))
        return res

    vevent_payment_terminal_mode = fields.Selection(
        [("card", "Card"), ("check", "Check")], string="Payment Mode", default="card"
    )
    vevent_payment_terminal_id = fields.Char(
        string="Terminal identifier",
        help=(
            "The identifier of the terminal as known by the hardware proxy. "
            "Leave empty if the proxy has only one terminal connected."
        ),
    )
