# -*- coding: utf-8 -*-
###################################################################################
#
#    Copyright (c) 2023-today Juan Carlos Flores.
#
#    This file is part of SMM_intecproof Module
#
#    This program is NOT a free software
#
###################################################################################
from odoo import _, api, exceptions, fields, models
from odoo.addons.bus.models.bus import channel_with_db, json_dump
import logging

_logger = logging.getLogger(__name__)

DEFAULT_MESSAGE = "Default message"

SUCCESS = "success"
DANGER = "danger"
WARNING = "warning"
INFO = "info"
DEFAULT = "default"


class ExtendResUsers(models.Model):
    _inherit = "res.users"

    # ----------------------------------------------------------
    # Definiciones de inicialización o valores
    # ----------------------------------------------------------
    @api.depends("create_date")
    def _compute_channel_names(self):
        for record in self:
            record.notify_success_channel_name = json_dump(
                channel_with_db(self.env.cr.dbname, record.partner_id)
            )
            record.notify_danger_channel_name = json_dump(
                channel_with_db(self.env.cr.dbname, record.partner_id)
            )
            record.notify_warning_channel_name = json_dump(
                channel_with_db(self.env.cr.dbname, record.partner_id)
            )
            record.notify_info_channel_name = json_dump(
                channel_with_db(self.env.cr.dbname, record.partner_id)
            )
            record.notify_default_channel_name = json_dump(
                channel_with_db(self.env.cr.dbname, record.partner_id)
            )

    # ----------------------------------------------------------
    # Base de datos
    # ----------------------------------------------------------
    evitar_cambios_dashboard = fields.Boolean('Evitar cambios en el tablero')
    notify_success_channel_name = fields.Char(compute="_compute_channel_names")
    notify_danger_channel_name = fields.Char(compute="_compute_channel_names")
    notify_warning_channel_name = fields.Char(compute="_compute_channel_names")
    notify_info_channel_name = fields.Char(compute="_compute_channel_names")
    notify_default_channel_name = fields.Char(compute="_compute_channel_names")

    def notify_success(
        self, message="Default message", title=None, sticky=False, target=None
    ):
        title = title or _("Evento completado")
        self._notify_channel(SUCCESS, message, title, sticky, target)

    def notify_danger(
        self, message="Default message", title=None, sticky=False, target=None
    ):
        title = title or _("Peligro")
        self._notify_channel(DANGER, message, title, sticky, target)

    def notify_warning(
        self, message="Default message", title=None, sticky=False, target=None
    ):
        title = title or _("Advertencia")
        self._notify_channel(WARNING, message, title, sticky, target)

    def notify_info(
        self, message="Mensaje", title=None, sticky=False, target=None
    ):
        title = title or _("Información")
        self._notify_channel(INFO, message, title, sticky, target)

    def notify_default(
        self, message="Mensaje", title=None, sticky=False, target=None
    ):
        title = title or _("Default")
        self._notify_channel(DEFAULT, message, title, sticky, target)

    def _notify_channel(self, type_message=DEFAULT, message=DEFAULT_MESSAGE, title=None, sticky=False, target=None):
        target = self.partner_id
        mensaje = {
            "type": type_message,
            "message": message,
            "title": title,
            "sticky": sticky,
        }

        notificacion = [[usuario, "web.notify", [mensaje]] for usuario in target]
        self.env["bus.bus"]._sendmany(notificacion)

