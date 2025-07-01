# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import logging
import tempfile
import binascii
import xmlrpc.client
from multiprocessing.spawn import import_main_path
import csv
from os.path import dirname, abspath
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import datetime
from odoo.tools.pycompat import csv_reader

_logger = logging.getLogger(__name__)
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')


class ResProductInh(models.Model):
    _inherit = 'product.supplierinfo'

    impa = fields.Char()


class ResProductInh(models.Model):
    _inherit = 'product.template'

    impa = fields.Char()


class ResCompanyInh(models.Model):
    _inherit = 'res.company'

    last_index = fields.Integer(default=0)
    updatecount = fields.Integer(string="Not Found",default=0)
    createcount = fields.Integer(default=0)
    total_impa = fields.Integer(default=0)
    vendor_id = fields.Integer(string="Vendor")
    pricelist_ids = fields.Char(string="pricelists")
    database=fields.Selection([('limani', 'Limani'), ('miq', 'Miq')], 'Database')
    file_data = fields.Binary("Upload XLSX File")

    def delete_vendor_pricelist(self):
        if self.env.company.database=='limani':
            url = 'https://portal.limanisupply.com'
            db = 'Limani_Supply'
            username = 'info@miqwebmedia.nl'
            password = 'WEw3hhFpv$&1pU3p5^7g'
        if self.env.company.database == 'miq':

            url = 'https://portal.miqconsumables.com'
            db = 'portal.miqconsumables.com'
            username = 'hunain'
            password = '123'

        if not self.env.company.database:
            raise UserError(_('Database Credentials are missing'))


        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

        vendor_id = self.env.company.vendor_id
        if not vendor_id:
            raise UserError(_('Vendor is missing'))

        supplierinfo_ids = models.execute_kw(db, uid, password, 'product.supplierinfo', 'search',
                                             [[['name', '=', vendor_id]]])

        # Step 2: Delete the matched pricelist items
        if supplierinfo_ids:
            models.execute_kw(db, uid, password,
                              'product.supplierinfo', 'unlink',
                              [supplierinfo_ids])
        _logger.info('---------------------------Deleted---------------=%s' % len([supplierinfo_ids]))


    def action_import_pricelist(self):
        if self.env.company.database == 'limani':
            url = 'https://portal.limanisupply.com'
            db = 'Limani_Supply'
            username = 'info@miqwebmedia.nl'
            password = 'WEw3hhFpv$&1pU3p5^7g'
        if self.env.company.database == 'miq':
            url = 'https://portal.miqconsumables.com'
            db = 'portal.miqconsumables.com'
            username = 'hunain'
            password = '123'

        if not self.env.company.database:
            raise UserError(_('Database Credentials are missing'))

        common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
        wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.file_data))
        counter = 0
        for s in wb.sheets():
            first_row = []
            for col in range(s.ncols):
                first_row.append(s.cell_value(0, col))
            header = ['VENDOR DESCRIPTION', 'VENDOR ARTICLE NUMBER', 'IMPA', 'PRICE']
            if first_row != header:
                raise ValidationError(_("File Header is not Proper"))

            data = []
            for row in range(1, s.nrows):
                elm = {}
                for col in range(s.ncols):
                    elm[first_row[col]] = s.cell_value(row, col)
                data.append(elm)

            # Validate vendor
            if not self.vendor_id or self.vendor_id == 0:
                raise ValidationError(_("Vendor ID is not Proper"))
            vendor_id = self.vendor_id
            row_no = 0
            last_index = self.env.company.last_index

            vals = []
            for rec in data:
                counter+=counter
                product_name = rec.get('VENDOR DESCRIPTION').strip()
                product_code = int(rec.get('VENDOR ARTICLE NUMBER')) if type(rec.get('VENDOR ARTICLE NUMBER')) == float else rec.get('VENDOR ARTICLE NUMBER').strip()
                impa = int(rec.get('IMPA')) if type(rec.get('IMPA')) == float else rec.get('IMPA').strip()
                price = float(rec.get('PRICE'))
                print(impa,price,counter,self.env.company.last_index)

                # category_name = int(line[4]) if type(line[4]) == float else line[4].strip()
                products = models.execute_kw(db, uid, password, 'product.template', 'search_read',
                                             [[['impa', '=', impa]]],
                                             {'fields': ['id', 'name', 'impa', 'seller_ids']})
                if not products:
                    self.env.company.updatecount+=1

                for product in products:
                    self.env.company.total_impa = self.env.company.total_impa + 1
                    if product and price > 0:
                        if vendor_id:
                            # vendorObj = models.execute_kw(db, uid, password, 'product.supplierinfo',
                            #                               'search_read', [[['name', '=',vendor_id],
                            #                                                ['impa', '=', impa]]],
                            #                               {'fields': ['id', 'preferred_vendor'], 'limit': 1})
                            # preferred_vendor = any(ven.get('preferred_vendor') for ven in vendorObj)
                            self.env.company.createcount += 1
                            vals = {

                                'name': vendor_id,
                                'product_name': product_name or False,
                                'product_desc': product_name or False,
                                'impa': impa,
                                'product_code': product_code or False,
                                'price': price or 0.0,
                                'product_tmpl_id': product.get('id'),
                                # 'preferred_vendor': preferred_vendor,
                            }

                            vendor_pricelist_id = models.execute_kw(db, uid, password, 'product.supplierinfo',
                                                                    'create', [vals])
                            self.env.cr.commit()

            row_no += 1
            last_index += 1


            # if counter == 5000:
            #     counter = 0
            #     self.env.company.last_index = last_index
            #     self.env.cr.commit()
            #     break
            self.env.company.last_index = last_index

            _logger.info('Updated: %s %s %s)', self.env.company.createcount,
                         self.env.company.total_impa, self.env.company.last_index)


        if last_index == len(data):
            self.env.company.last_index=0
            _logger.info('----------------File completed------------------------')




