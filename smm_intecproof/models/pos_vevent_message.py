from odoo import models, fields 

class PosVeventMessage(models.Model):
      _name = 'pos.vevent.message'

      session_id = fields.Char(string='Session ID')
      pos_name = fields.Char(string='POS Name')
      json_request = fields.Char(string='JSON Request')
      json_response = fields.Char(string='JSON Response')
      transaction_id = fields.Char(string='Transaction ID')