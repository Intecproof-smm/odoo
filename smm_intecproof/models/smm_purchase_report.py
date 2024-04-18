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

from odoo import models, fields, api
import io
import json
import logging

_logger = logging.getLogger(__name__)

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DynamicPurchaseReport(models.Model):
    _name = "dynamic.purchase.report"

    purchase_report = fields.Char(string="Purchase Report")
    date_from = fields.Datetime(string="Date From")
    date_to = fields.Datetime(string="Date to")
    report_type = fields.Selection([
        ('report_by_order', 'Por orden de compra'),
        ('report_by_order_detail', 'Por orden de compra detalle'),
        ('report_by_product', 'Por producto'),
        ('report_by_categories', 'Por categoría'),
        ('report_by_purchase_representative', 'Por usuario'),
        ('report_by_supplier', 'Por proveedor'),
        ('report_by_state', 'Por estatus')], default='report_by_order')

    @api.model
    def purchase_report(self, option):
        orders = self.env['purchase.order'].search([])
        report_values = self.env['dynamic.purchase.report'].search(
            [('id', '=', option[0])])
        data = {
            'report_type': report_values.report_type,
            'model': self,
        }

        if report_values.date_from:
            data.update({
                'date_from': report_values.date_from,
            })
        if report_values.date_to:
            data.update({
                'date_to': report_values.date_to,
            })
        filters = self.get_filter(option)
        report = self._get_report_values(data)
        lines = self._get_report_values(data).get('PURCHASE')

        return {
            'name': "Purchase Orders",
            'type': 'ir.actions.client',
            'tag': 's_r',
            'orders': data,
            'filters': filters,
            'report_lines': lines,
        }

    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}
        if data.get('report_type') == 'report_by_order':
            filters['report_type'] = 'Por orden de compra'
        elif data.get('report_type') == 'report_by_order_detail':
            filters['report_type'] = 'Por orden de compra (Detalle)'
        elif data.get('report_type') == 'report_by_product':
            filters['report_type'] = 'Por producto'
        elif data.get('report_type') == 'report_by_categories':
            filters['report_type'] = 'Por categoría'
        elif data.get('report_type') == 'report_by_purchase_representative':
            filters['report_type'] = 'Por usuario'
        elif data.get('report_type') == 'report_by_state':
            filters['report_type'] = 'Por estatus'
        elif data.get('report_type') == 'report_by_supplier':
            filters['report_type'] = 'Por proveedor'
        else:
            filters['report_type'] = 'Por orden de compra'

        return filters

    def get_filter_data(self, option):
        r = self.env['dynamic.purchase.report'].search([('id', '=', option[0])])
        default_filters = {}

        filter_dict = {
            'report_type': r.report_type,
        }
        filter_dict.update(default_filters)
        return filter_dict

    @api.model
    def create(self, vals):

        res = super(DynamicPurchaseReport, self).create(vals)
        return res

    def write(self, vals):
        res = super(DynamicPurchaseReport, self).write(vals)
        return res

    def _get_report_sub_lines(self, data, report, date_from, date_to):
        report_sub_lines = []
        new_filter = None

        if data.get('report_type') == 'report_by_order':
            query = '''
                     select l.name,l.date_order,l.partner_id,l.amount_total,l.notes,l.user_id,res_partner.name as partner,
                              res_users.partner_id as user_partner,sum(purchase_order_line.product_qty),l.id as id,
                             (SELECT res_partner.name as salesman FROM res_partner WHERE res_partner.id = res_users.partner_id)
                             from purchase_order as l
                             left join res_partner on l.partner_id = res_partner.id
                             left join res_users on l.user_id = res_users.id
                             left join purchase_order_line on l.id = purchase_order_line.order_id
                              '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by l.user_id,res_users.partner_id,res_partner.name,l.partner_id,l.date_order,l.name,l.amount_total,l.notes,l.id"
            self._cr.execute(query)
            report_by_order = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order)
        elif data.get('report_type') == 'report_by_order_detail':
            query = '''
               select l.name,l.date_order,l.partner_id,l.amount_total,l.notes,l.user_id,res_partner.name as partner,
                      res_users.partner_id as user_partner,sum(purchase_order_line.product_qty), purchase_order_line.name as product, purchase_order_line.price_unit,purchase_order_line.price_subtotal,l.amount_total,purchase_order_line.product_id,product_product.default_code,
                      (SELECT res_partner.name as salesman FROM res_partner WHERE res_partner.id = res_users.partner_id)
                      from purchase_order as l
                      left join res_partner on l.partner_id = res_partner.id
                      left join res_users on l.user_id = res_users.id
                      left join purchase_order_line on l.id = purchase_order_line.order_id
                     left join product_product on purchase_order_line.product_id = product_product.id
                    '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by l.user_id,res_users.partner_id,res_partner.name,l.partner_id,l.date_order,l.name,l.amount_total,l.notes,purchase_order_line.name,purchase_order_line.price_unit,purchase_order_line.price_subtotal,l.amount_total,purchase_order_line.product_id,product_product.default_code"
            self._cr.execute(query)
            report_by_order_details = self._cr.dictfetchall()
            report_sub_lines.append(report_by_order_details)
        elif data.get('report_type') == 'report_by_product':
            query = '''
            select l.amount_total,sum(purchase_order_line.product_qty) as qty, purchase_order_line.name as product, purchase_order_line.price_unit,product_product.default_code,product_category.name
                     from purchase_order as l
                     left join purchase_order_line on l.id = purchase_order_line.order_id
                     left join product_product on purchase_order_line.product_id = product_product.id
                     left join product_template on purchase_order_line.product_id = product_template.id
                     left join product_category on product_category.id = product_template.categ_id
                               '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
                term = 'AND '
            query += term + "product_category.name = 'Medicamentos' "
            query += "group by l.amount_total,purchase_order_line.name,purchase_order_line.price_unit,purchase_order_line.product_id,product_product.default_code,product_template.categ_id,product_category.name "
            query += "order by purchase_order_line.name"
            self._cr.execute(query)
            report_by_product = self._cr.dictfetchall()
            report_sub_lines.append(report_by_product)
        elif data.get('report_type') == 'report_by_supplier':
            query = '''
               select l.name,l.date_order,l.partner_id,l.amount_total,l.notes,l.user_id,res_partner.name as partner,
                          res_users.partner_id as user_partner,sum(purchase_order_line.product_qty), purchase_order_line.name as product, purchase_order_line.price_unit,purchase_order_line.price_subtotal,l.amount_total,purchase_order_line.product_id,product_product.default_code,product_category.name as categoria,
                          (SELECT res_partner.name as salesman FROM res_partner WHERE res_partner.id = res_users.partner_id)
                          from purchase_order as l
                          left join res_partner on l.partner_id = res_partner.id
                          left join res_users on l.user_id = res_users.id
                          left join purchase_order_line on l.id = purchase_order_line.order_id
                          left join product_product on purchase_order_line.product_id = product_product.id
                          left join product_template on purchase_order_line.product_id = product_template.id
                          left join product_category on product_category.id = product_template.categ_id
                          
                        '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
                term = 'AND '
            query += term + "product_category.name = 'Medicamentos' "
            query += "group by l.user_id,res_users.partner_id,res_partner.name,l.partner_id,l.date_order,l.name,l.amount_total,l.notes,purchase_order_line.name,purchase_order_line.price_unit,purchase_order_line.price_subtotal,l.amount_total,purchase_order_line.product_id,product_product.default_code,product_category.name"
            query += " order by res_partner.name,l.name,l.date_order"
            self._cr.execute(query)
            _logger.info("********* Contenido de SELF previo: %s", self)
            report_by_supplier = self._cr.dictfetchall()
            _logger.info("********* Contenido de SELF Posterior: %s", report_by_supplier)
            report_sub_lines.append(report_by_supplier)
        elif data.get('report_type') == 'report_by_categories':
            query = '''
            select product_category.name,sum(l.product_qty) as qty,sum(l.price_subtotal) as amount_total
                     from purchase_order_line as l
                     left join product_template on l.product_id = product_template.id
                     left join product_category on product_category.id = product_template.categ_id
                     left join purchase_order on l.order_id = purchase_order.id
            '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where purchase_order.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "purchase_order.date_order <= '%s' " % data.get('date_to')
            query += "group by product_category.name"
            self._cr.execute(query)
            report_by_categories = self._cr.dictfetchall()
            report_sub_lines.append(report_by_categories)
        elif data.get('report_type') == 'report_by_purchase_representative':
            query = '''
           select res_partner.name,sum(purchase_order_line.product_qty) as qty,sum(purchase_order_line.price_subtotal) as amount,count(l.id) as order
                    from purchase_order as l
                    left join res_users on l.user_id = res_users.id
                    left join res_partner on res_users.partner_id = res_partner.id
                    left join purchase_order_line on l.id = purchase_order_line.order_id
           '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by res_partner.name"
            self._cr.execute(query)
            report_by_purchase_representative = self._cr.dictfetchall()
            report_sub_lines.append(report_by_purchase_representative)

        elif data.get('report_type') == 'report_by_state':
            query = '''
                       select l.state,sum(purchase_order_line.product_qty) as qty,sum(purchase_order_line.price_subtotal) as amount,count(l.id) as order
                    from purchase_order as l
                    left join res_users on l.user_id = res_users.id
                    left join res_partner on res_users.partner_id = res_partner.id
                    left join purchase_order_line on l.id = purchase_order_line.order_id
                    '''
            term = 'Where '
            if data.get('date_from'):
                query += "Where l.date_order >= '%s' " % data.get('date_from')
                term = 'AND '
            if data.get('date_to'):
                query += term + "l.date_order <= '%s' " % data.get('date_to')
            query += "group by l.state"
            self._cr.execute(query)
            report_by_state = self._cr.dictfetchall()

            report_sub_lines.append(report_by_state)
        return report_sub_lines

    def _get_report_values(self, data):
        docs = data['model']
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        if data['report_type'] == 'report_by_order_detail':
            report = ['Por orden de compra (Detalle)']
        elif data['report_type'] == 'report_by_product':
            report = ['Por producto']
        elif data['report_type'] == 'report_by_categories':
            report = ['Por categoría']
        elif data['report_type'] == 'report_by_purchase_representative':
            report = ['Por usuario']
        elif data['report_type'] == 'report_by_state':
            report = ['Por estatus']
        elif data['report_type'] == 'report_by_supplier':
            report = ['Por proveedor']
        else:
            report = ['Por orden de compra']

        if data.get('report_type'):
            report_res = self._get_report_sub_lines(data, report, date_from, date_to)[0]
        else:
            report_res = self._get_report_sub_lines(data, report, date_from, date_to)

        return {
            'doc_ids': self.ids,
            'docs': docs,
            'PURCHASE': report_res,
        }

    def get_purchase_xlsx_report(self, data, response, report_data, dfr_data):
        report_data_main = json.loads(report_data)
        output = io.BytesIO()
        filters = json.loads(data)

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})
        sub_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 2,
             'border_color': 'black'})
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_l = workbook.add_format(
            {'font_size': '10px', 'border': 1, 'bold': True})
        txt_v = workbook.add_format(
            {'align': 'right', 'font_size': '10px', 'border': 1})
        sheet.merge_range('A2:H3',
                          'Reporte de Compras',
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})
        date_style = workbook.add_format({'align': 'center',
                                          'font_size': '10px'})

        if filters.get('report_type') == 'report_by_order':

            sheet.merge_range('B5:D5', 'Tipo de reporte: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Orden de compra', heading)
            sheet.write('B7', 'Fecha', heading)
            sheet.write('C7', 'Proveedor', heading)
            sheet.write('D7', 'Usuario', heading)
            sheet.write('E7', 'Cantidad', heading)
            sheet.write('F7', 'Total', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 0
            sheet.set_column(3, 0, 15)
            sheet.set_column(4, 1, 15)
            sheet.set_column(5, 2, 15)
            sheet.set_column(6, 3, 15)
            sheet.set_column(7, 4, 15)
            sheet.set_column(8, 5, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['date_order'], txt_l)
                sheet.write(row, col + 2, rec_data['partner'], txt_l)
                sheet.write(row, col + 3, rec_data['salesman'], txt_l)
                sheet.write(row, col + 4, rec_data['sum'], txt_l)
                sheet.write(row, col + 5, rec_data['amount_total'], txt_l)

        if filters.get('report_type') == 'report_by_order_detail':

            sheet.merge_range('B5:D5', 'Tipo de reporte: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Orden de compra', heading)
            sheet.write('B7', 'Fecha', heading)
            sheet.write('C7', 'Proveedor', heading)
            sheet.write('D7', 'Usuario', heading)
            sheet.write('E7', 'Producto', heading)
            sheet.write('F7', 'Descripción', heading)
            sheet.write('G7', 'Precio Unitario', heading)
            sheet.write('H7', 'Cantidad', heading)
            sheet.write('I7', 'Total', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 0
            sheet.set_column(3, 0, 15)
            sheet.set_column(4, 1, 15)
            sheet.set_column(5, 2, 15)
            sheet.set_column(6, 3, 15)
            sheet.set_column(7, 4, 15)
            sheet.set_column(8, 5, 15)
            sheet.set_column(9, 6, 15)
            sheet.set_column(10, 7, 15)
            sheet.set_column(11, 8, 15)
            sheet.set_column(12, 9, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['date_order'], txt_l)
                sheet.write(row, col + 2, rec_data['partner'], txt_l)
                sheet.write(row, col + 3, rec_data['salesman'], txt_l)
                sheet.write(row, col + 4, rec_data['default_code'], txt_l)
                sheet.write(row, col + 5, rec_data['product'], txt_l)
                sheet.write(row, col + 6, rec_data['price_unit'], txt_l)
                sheet.write(row, col + 7, rec_data['sum'], txt_l)
                sheet.write(row, col + 8, rec_data['amount_total'], txt_l)

        if filters.get('report_type') == 'report_by_supplier':

            sheet.merge_range('B5:D5', 'Tipo de reporte: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Proveedor', heading)
            sheet.write('B7', 'Compra', heading)
            sheet.write('C7', 'Fecha', heading)
            sheet.write('D7', 'Usuario', heading)
            sheet.write('E7', 'Producto', heading)
            sheet.write('F7', 'Cantidad', heading)
            sheet.write('G7', 'Precio Unitario', heading)
            sheet.write('H7', 'Total', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 0
            sheet.set_column(3, 0, 15)
            sheet.set_column(4, 1, 15)
            sheet.set_column(5, 2, 15)
            sheet.set_column(6, 3, 15)
            sheet.set_column(7, 4, 15)
            sheet.set_column(8, 5, 15)
            sheet.set_column(9, 6, 15)
            sheet.set_column(10, 7, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['partner'], txt_l)
                sheet.write(row, col + 1, rec_data['name'], txt_l)
                sheet.write(row, col + 2, rec_data['date_order'], txt_l)
                sheet.write(row, col + 3, rec_data['salesman'], txt_l)
                sheet.write(row, col + 4, rec_data['product'], txt_l)
                sheet.write(row, col + 5, rec_data['sum'], txt_l)
                sheet.write(row, col + 6, rec_data['price_unit'], txt_l)
                sheet.write(row, col + 7, rec_data['price_subtotal'], txt_l)

        if filters.get('report_type') == 'report_by_product':

            sheet.merge_range('B5:D5', 'Tipo de reporte: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Categoría', heading)
            sheet.write('B7', 'Producto', heading)
            sheet.write('C7', 'Descripción', heading)
            sheet.write('D7', 'Cantidad', heading)
            sheet.write('E7', 'Total', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 0
            sheet.set_column(3, 0, 15)
            sheet.set_column(4, 1, 15)
            sheet.set_column(5, 2, 15)
            sheet.set_column(6, 3, 15)
            sheet.set_column(7, 4, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['default_code'], txt_l)
                sheet.write(row, col + 2, rec_data['product'], txt_l)
                sheet.write(row, col + 3, rec_data['qty'], txt_l)
                sheet.write(row, col + 4, rec_data['amount_total'], txt_l)

        if filters.get('report_type') == 'report_by_categories':

            sheet.merge_range('B5:D5', 'Tipo de reporte: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('B7', 'Categoría', heading)
            sheet.write('C7', 'Cantidad', heading)
            sheet.write('D7', 'Total', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 1
            sheet.set_column(3, 1, 15)
            sheet.set_column(4, 2, 15)
            sheet.set_column(5, 3, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['qty'], txt_l)
                sheet.write(row, col + 2, rec_data['amount_total'], txt_l)

        if filters.get('report_type') == 'report_by_purchase_representative':

            sheet.merge_range('B5:D5', 'Tipo de reporte: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Usuario', heading)
            sheet.write('B7', 'Total de ordenes de compra', heading)
            sheet.write('C7', 'Total en cantidades', heading)
            sheet.write('D7', 'Total en importe', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 0
            sheet.set_column(3, 0, 15)
            sheet.set_column(4, 1, 15)
            sheet.set_column(5, 2, 15)
            sheet.set_column(6, 3, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                sheet.write(row, col, rec_data['name'], txt_l)
                sheet.write(row, col + 1, rec_data['order'], txt_l)
                sheet.write(row, col + 2, rec_data['qty'], txt_l)
                sheet.write(row, col + 3, rec_data['amount'], txt_l)

        if filters.get('report_type') == 'report_by_state':

            sheet.merge_range('B5:D5', 'Tipo de reporte: ' +
                              filters.get('report_type'), txt_l)

            sheet.write('A7', 'Estatus', heading)
            sheet.write('B7', 'Total de ordenes de compra', heading)
            sheet.write('C7', 'Cantidades', heading)
            sheet.write('D7', 'Importes', heading)

            lst = []
            for rec in report_data_main[0]:
                lst.append(rec)
            row = 6
            col = 0
            sheet.set_column(3, 0, 15)
            sheet.set_column(4, 1, 15)
            sheet.set_column(5, 2, 15)
            sheet.set_column(6, 3, 15)

            for rec_data in report_data_main:
                one_lst = []
                two_lst = []
                row += 1
                if rec_data['state'] == 'draft':
                    sheet.write(row, col, 'Pendiente', txt_l)
                elif rec_data['state'] == 'sent':
                    sheet.write(row, col, 'Enviado', txt_l)
                elif rec_data['state'] == 'purchase':
                    sheet.write(row, col, 'Orden de compra', txt_l)
                sheet.write(row, col + 1, rec_data['order'], txt_l)
                sheet.write(row, col + 2, rec_data['qty'], txt_l)
                sheet.write(row, col + 3, rec_data['amount'], txt_l)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
