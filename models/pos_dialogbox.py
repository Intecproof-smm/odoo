from odoo import models, fields

class pos_dialogbox(models.TransientModel):
    _name = "pos.dialogbox"

    x_turno = fields.Selection(
        selection = [
            ('m', 'Matutino (M)')
            , ('v', 'Vespertino (V)')
            , ('n1', 'Nocturno 1 (N1)')
            , ('n2', 'Nocturno 2 (N2)')
            , ('ja', 'Jornada Acumulada (JA)')
            , ('jf', 'Jornada Festiva (JF)')
        ]
        , string = 'Turno'
        , required = True
    )

    config_id = fields.Integer()

    def btn_yes(self):
        pos_config = self.env['pos.config'].browse(self.config_id)
        return pos_config.abre_sesion_con_turno(self.x_turno)
