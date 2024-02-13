from odoo import models, fields

# Clase que extende el modelo pos.order para agregar propiedades que se 
# necesitan para las salidas de inventario
class PosConfigSmm(models.Model):
    _inherit = "pos.config"

    turno_sel = fields.Char(store=False)

    def open_ui(self):
        if not self.current_session_id:
            value = self.env['pos.dialogbox'].sudo().create({'x_turno':'m', 'config_id':self.id})
            return {
                'name':'Seleccione el turno',
                'type':'ir.actions.act_window',
                'res_model':'pos.dialogbox',
                'view_type':'form',
                'view_mode':'form',
                'target':'new',
                'res_id':value.id                
            }
        else:
            return self.main_open_ui()

    # Este código fue obtenido de la clase original y adaptado al requerimiento.
    # En caso de que se actualice la versión de Odoo será necesario revisar y volver
    # a implementar este código en caso de haber sufrido cambios.
    def _action_to_open_ui(self):
        if not self.current_session_id:
            if not self.turno_sel:
                raise ValueError("No se ha especificado el turno para la sesión.")
            else:
                self.env['pos.session'].create({'user_id': self.env.uid, 'config_id': self.id, 'x_turno': self.turno_sel})
        path = '/pos/web' if self._force_http() else '/pos/ui'
        return {
            'type': 'ir.actions.act_url',
            'url': path + '?config_id=%d' % self.id,
            'target': 'self',
        }

    def main_open_ui(self):
        return super().open_ui()

    def abre_sesion_con_turno(self, turno):
        self.turno_sel = turno
        return self.main_open_ui()
        