import logging

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_area_solicitud = fields.Selection(
        selection = [
            ('urg', 'Urgencias')
            , ('hp', 'Hospital')
            , ('cons', 'Consulta')
            , ('uci', 'UCI')
            , ('quir', 'Quirofano')
        ]
        , string = 'Área que solicita'
        , store = True
    )
    name = fields.Char(readonly=False) ########################   habiitar temporal para migracion  ###########################################################

    x_cama = fields.Char(string = 'Cama', store = True)
    x_fecha_nacimiento = fields.Date(
        string = 'Fecha de nacimiento',
        related = 'partner_id.x_fecha_nacimiento',
        store = True
    )
    x_no_ambulancia = fields.Char(string = 'Ambulancia', store = True)
    x_solicitante = fields.Many2one('res.partner', string = 'Solicitante', store = True)
    x_receta = fields.Char(string = 'Receta', store = True)
    x_indicacion = fields.Char(string = 'Indicación', store = True)

    x_turno = fields.Selection(
        selection = [
            ('m', 'M')
            , ('v', 'V')
            , ('n1', 'N1')
            , ('n2', 'N2')
            , ('ja', 'JA')
        ]
        , string = 'Turno'
        , store = True
    )

    x_branches_pk = fields.Many2many('res.branch', string='Almacenes permitidos',
                                        relation='x_res_branch_stock_picking_rel',related='location_id.x_branches', column1="stock_picking_id", column2="res_branch_id",
                                        store=False, readonly=True)

    x_permiso_validar = fields.Boolean(string='Permiso para validacion', store=False,readonly=True,
                                    compute='_compute_permiso')

    has_controlled_product = fields.Boolean(string = "Tiene producto controlado", store = True)

    def _get_default_branch_id(self):
        return self.env.user.branch_id

    branch_id = fields.Many2one(
        "res.branch", string='Branch', readonly=False, store=True, compute="_compute_branch_id", default=_get_default_branch_id
    )

    @api.depends('company_id', 'sale_id', 'purchase_id')
    def _compute_branch_id(self):
        """methode to compute branch"""
        for record in self:
            record.branch_id = self.env.user.branch_id

    @api.onchange("x_permiso_validar")
    def _compute_permiso(self):
        for record in self:
             record['x_permiso_validar'] = False
             if self.env.user['x_validar_salidas']:
                   record['x_permiso_validar'] = True

    @api.model
    def create(self, vals):
        _logger.info(vals)

        current_user = self.env['res.users'].browse(self.env.user.id)

        picking_type_id = vals['picking_type_id']
        picking_type = self.env['stock.picking.type'].browse(picking_type_id)

        location_id = vals['location_id']
        location = self.env['stock.location'].browse(location_id)

        location_dest_id = vals['location_dest_id']
        location_dest = self.env['stock.location'].browse(location_dest_id)

        _logger.info('Validacion de permiso de usuario al crear - ' + str(current_user.login))
        _logger.info('location_id: ' + str(location))
        _logger.info('location_id.x_branch: ' + str(location.x_branch))
        _logger.info('location_dest_id: ' + str(location_dest))
        _logger.info('location_dest_id.x_branch: ' + str(location_dest.x_branch))
        _logger.info(str(True if location_dest.x_branch else False))
        _logger.info('current_user.branch_id: ' + str(current_user.branch_id))
        _logger.info('picking_type.code: ' + str(picking_type.code))

        is_controlled_product = False

        if 'has_controlled_product' in vals:
            is_controlled_product = vals['has_controlled_product']

        # validacion de productos no controlados
        wrong_products = self.__validar_productos_controlados(vals, is_controlled_product)

        if len(wrong_products) > 0:
            mensaje_error = 'La solicitud solo debe de contener productos ' \
                            + ('controlados.' if vals['has_controlled_product'] else ' no controlados.')

            raise UserError(mensaje_error)

        # validacion de permisos
        if current_user.x_ignorar_restriccion_default_branch is True:
            return super(StockPicking, self).create(vals)

        # al crear mis solicitudes internas
        if picking_type.code == 'internal':
            # devolucion de solicitud
            if 'origin' in vals:
                return super(StockPicking, self).create(vals)

            if location_dest.x_branch.id is False:
                raise ValidationError('La ubicación destino no tiene branch configurado')

            if location_dest.x_branch.id != current_user.branch_id.id:
                raise ValidationError('No puedes crear solicitudes que no tengan como destino tu branch')

            return super(StockPicking, self).create(vals)

        # al crear recepciones de proveedor
        if picking_type.code == 'incoming':
            if location.usage == 'supplier':
                if location_dest.x_branch.id is False:
                    raise ValidationError('La ubicación destino no tiene branch configurado')

                if location_dest.x_branch.id != current_user.branch_id.id:
                    raise ValidationError(
                        'No puedes crear recepciones de proveedor que no tengan como destino tu branch'
                    )

        return super(StockPicking, self).create(vals)

    def write(self, vals):
        _logger.info(vals)
        current_user = self.env['res.users'].browse(self.env.user.id)

        is_controlled_product = None

        if self.id:
            # validacion de productos no controlados
            if 'has_controlled_product' in vals:
                is_controlled_product = vals['has_controlled_product']
            else:
                is_controlled_product = self.has_controlled_product

            # siempre verificar que las lineas respeten la configuracion de la cabecera
            if 'move_ids_without_package' in vals:
                stock_picking = vals
            else:
                stock_picking = {'move_ids_without_package': []}

                for move in self.move_ids_without_package:
                    stock_picking['move_ids_without_package'].append([0, 0, {'product_id': move.product_id.id}])

            wrong_products = self.__validar_productos_controlados(stock_picking, is_controlled_product)

            if len(wrong_products) > 0:
                mensaje_error = 'La solicitud solo debe de contener productos '\
                                + ('controlados.' if is_controlled_product else ' no controlados.')

                raise UserError(mensaje_error)

        # validacion de permisos
        _logger.info('Validacion de permiso de usuario al actualizar - ' + str(current_user.login))
        _logger.info(vals)
        _logger.info('id: ' + str(self.id))
        _logger.info('location_id: ' + str(self.location_id))
        _logger.info('location_id.x_branch: ' + str(self.location_id.x_branch))
        _logger.info('location_dest_id: ' + str(self.location_dest_id))
        _logger.info('location_dest_id.x_branch: ' + str(self.location_dest_id.x_branch))
        _logger.info(str(True if self.location_dest_id.x_branch else False))
        _logger.info('branch_id: ' + str(self.branch_id))
        _logger.info('current_user.branch_id: ' + str(current_user.branch_id))

        # se necesita al confirmar salidas de mercancia de traslados solicitados
        if self.id is False:
            return super(StockPicking, self).write(vals)

        if current_user.x_ignorar_restriccion_default_branch is True:
            return super(StockPicking, self).write(vals)

        # solicitudes internas, soy el destino
        if self.picking_type_id.code == 'internal':
            # el origen es quien comprueba la disponibilidad y valida(hecho)
            if self.location_id.x_branch is False:
                raise ValidationError('La ubicacion origen no tiene branch configurado')

            if self.location_id.x_branch.id == current_user.branch_id.id:
                return super(StockPicking, self).write(vals)

            # destino es quien genera la solicitud y puede actualizar siempre y cuando se encuentre en borrador
            if self.location_dest_id.x_branch is False:
                raise ValidationError('La ubicación destino no tiene branch configurado')

            if self.location_dest_id.x_branch.id != current_user.branch_id.id:
                raise ValidationError('No puedes modificar solicitudes que no tengan como destino tu branch')

            if self.state != 'draft':
                raise ValidationError('Solo puedes modificar solicitudes en borrador')

            return super(StockPicking, self).write(vals)

        # recepciones de proveedor, soy el destino
        if self.picking_type_id.code == 'incoming':
            if self.location_id.usage == 'supplier':
                if self.location_dest_id.x_branch.id is False:
                    raise ValidationError('La ubicación destino no tiene branch configurado')

                if self.location_dest_id.x_branch.id != current_user.branch_id.id:
                    raise ValidationError(
                        'No puedes modificar recepciones de proveedor que no tengan como destino tu branch'
                    )

                return super(StockPicking, self).write(vals)

        # devolucion de orden de entrega, yo soy el destino
        if self.location_id.usage == 'customer':
            if self.location_dest_id.x_branch.id is False:
                raise ValidationError('La ubicación destino no tiene branch configurado')

            if self.location_dest_id.x_branch.id != current_user.branch_id.id:
                raise ValidationError('No puedes modificar registros que no pertenecen a tu branch')

            return super(StockPicking, self).write(vals)

        # ordenes de entrega, yo soy el origen
        if self.location_id.x_branch.id is False:
            raise ValidationError('La ubicación origen no tiene branch configurado')

        if self.location_id.x_branch.id != current_user.branch_id.id:
            raise ValidationError('No puedes modificar registros que no pertenecen a tu branch')

        return super(StockPicking, self).write(vals)

    def button_validate(self):
        current_user = self.env['res.users'].browse(self.env.user.id)

        for line in self.move_line_ids_without_package:
            line.product_id.location_org = self.location_id.id
            line.product_id.location_des = self.location_dest_id.id

        # validacion de negativos
        stock_picking = self.env['stock.picking'].browse(self.id)
        _logger.info('Validando negativos ' + str(stock_picking))
        negative_products = self.__validar_negativos(stock_picking)

        if len(negative_products) > 0:
            products_str = ', '.join(negative_products)

            raise ValidationError(
                'No esta permitida la existencia negativa en los siguientes productos: ' + products_str
            )

        # saltarse la validacion de expirados
        if current_user.x_ignorar_restriccion_default_branch is True:
            self = self.with_context(skip_expired = True)

            return super(StockPicking, self).button_validate()

        # al validar solicitudes internas que me hacen
        if self.picking_type_id.code == 'internal':
            if self.location_id.x_branch.id is False:
                raise ValidationError('La ubicación origen no tiene branch configurado')

            if self.location_id.x_branch.id != current_user.branch_id.id:
                raise ValidationError('No puedes validar solicitudes que no tengan como origen tu branch')

        return super(StockPicking, self).button_validate()

    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()

        for move in self.move_ids_without_package:
            producto_encontrado = False
            for linea in self.move_line_ids_without_package:
                if linea.product_id.id == move.product_id.id:
                    producto_encontrado = True
            if not producto_encontrado:
                move.state = 'waiting'

        # When marking as 'to be done' transfer requests, suggest lots that are closest to expiration
        # , with expired ones as the last option.
        if self.picking_type_id.code == 'internal':
            if self.location_id != self.location_dest_id:
                stock_picking_button_assign_wizard = self.env['stock.picking.button.assign.wizard'].create(
                    {
                        'stock_picking_id': self.id
                    }
                )

                return stock_picking_button_assign_wizard.confirm_action_assign()

        return res

    def action_assign(self):
        current_user = self.env['res.users'].browse(self.env.user.id)

        if current_user.x_ignorar_restriccion_default_branch is True:
            view = self.env.ref('smm_odoo.view_smm_stock_picking_button_validate_wizard')
            wiz = self.env['stock.picking.button.assign.wizard'].create(
                {
                    'stock_picking_id': self.id
                }
            )

            return {
                'name':        ('Advertencia')
                , 'type':      'ir.actions.act_window'
                , 'view_type': 'form'
                , 'view_mode': 'form'
                , 'res_model': 'stock.picking.button.assign.wizard'
                , 'views':     [(view.id, 'form')]
                , 'view_id':   view.id
                , 'target':    'new'
                , 'res_id':    wiz.id
            }

        # al comprobar disponibilidad de solicitudes internas que me hacen
        if self.picking_type_id.code == 'internal':
            if self.location_id.x_branch.id is False:
                raise ValidationError('La ubicación origen no tiene branch configurado')

            if self.location_id.x_branch.id != current_user.branch_id.id:
                raise ValidationError(
                    'No puedes comprobar disponibilidad de solicitudes que no tengan como origen tu branch'
                )

        view = self.env.ref('smm_odoo.view_smm_stock_picking_button_validate_wizard')
        wiz = self.env['stock.picking.button.assign.wizard'].create(
            {
                'stock_picking_id': self.id
            }
        )

        return {
            'name':        ('Advertencia')
            , 'type':      'ir.actions.act_window'
            , 'view_type': 'form'
            , 'view_mode': 'form'
            , 'res_model': 'stock.picking.button.assign.wizard'
            , 'views':     [(view.id, 'form')]
            , 'view_id':   view.id
            , 'target':    'new'
            , 'res_id':    wiz.id
        }

    def action_cancel(self):
        current_user = self.env['res.users'].browse(self.env.user.id)

        if current_user.x_ignorar_restriccion_default_branch is True:

            #do_unreserve
            self.move_ids._do_unreserve() #se cambia move_line por move_ids 211023
            self.package_level_ids.filtered(lambda p: not p.move_ids).unlink()

            return super(StockPicking, self).action_cancel()

        # al cancelar solicitudes internas que me hacen
        if self.picking_type_id.code == 'internal':
            if self.location_id.x_branch.id is False:
                raise ValidationError('La ubicación origen no tiene branch configurado')

            if self.location_id.x_branch.id != current_user.branch_id.id:
                raise ValidationError(
                    'No puedes cancelar solicitudes que no tengan como origen tu almacen'
                )
        #do_unreserve
        self.move_ids._do_unreserve() #se cambia move_line por move_ids 211023
        self.package_level_ids.filtered(lambda p: not p.move_ids).unlink()#se cambia move_line por move_ids 211023

        return super(StockPicking, self).action_cancel()

    def __validar_productos_controlados(self, stock_picking, is_controlled_product):
        wrong_products = []

        if 'move_ids_without_package' in stock_picking:
            for linea in stock_picking['move_ids_without_package']:
                if linea[2]:
                    if 'product_id' in linea[2]:
                        product_id = linea[2]['product_id']
                        product = self.env['product.product'].browse(product_id)

                        if is_controlled_product != product.is_controlled_product:
                            wrong_products.append(product)

        return wrong_products

    def __validar_negativos(self, stock_picking):
        # verificar linea por linea si se va a quedar en Negativo
        # se debe de tomar el quant del almacen que se va a descontar la mercancia
        # en caso de que no exista que lo tome como negativo

        negative_products = []
        decimal_precision = self.env["decimal.precision"].precision_get("Product Unit of Measure")

        # _logger.info(str(stock_picking.move_line_ids_without_package))

        for line in stock_picking.move_line_ids_without_package:
            # _logger.info(str(line.product_id.id))
            # _logger.info(str(line.location_id.id))
            # _logger.info(str(line.lot_id.id))

            quant = self.env['stock.quant'].search(
                [
                    ('product_id', '=', line.product_id.id)
                    , ('location_id', '=', line.location_id.id)
                    , ('lot_id', '=', line.lot_id.id)
                ]
            )

            if quant is False:
                # Que pasa si no existe un registro en stock quant de ese producto?
                negative_products.append(line.product_id.default_code)
                continue

            disallowed_by_product = (
                not quant.product_id.allow_negative_stock
                and not quant.product_id.categ_id.allow_negative_stock
            )
            disallowed_by_location = not quant.location_id.allow_negative_stock

            movimiento_entrada = False
            if (quant.product_id.location_org == quant.product_id.location_des):
                movimiento_entrada = True

            # _logger.info(str(disallowed_by_product))
            # _logger.info(str(disallowed_by_location))
            # _logger.info(str(movimiento_entrada))
            # _logger.info(str(quant.quantity))

            if (
                (float_compare(quant.quantity - line.qty_done, 0, precision_digits = decimal_precision) == -1
                   # and float_compare(quant.available_quantity - line.qty_done, 0, precision_digits = decimal_precision) == -1
                )
                and quant.product_id.type == "product"
                and quant.location_id.usage in ["internal", "transit"]
                and disallowed_by_product
                and disallowed_by_location
                and not movimiento_entrada
            ):
                negative_products.append(line.product_id.default_code)

        return negative_products

