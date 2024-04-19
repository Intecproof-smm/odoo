from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    """inherited purchase order"""
    _inherit = 'purchase.order'


    effective_date = fields.Date(readonly=False)
    date_approve = fields.Datetime('Confirmation Date', readonly=False, index=True, copy=False)
