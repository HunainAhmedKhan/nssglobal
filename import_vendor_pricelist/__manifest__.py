# -*- coding: utf-8 -*-
{
    'name' : 'Import Vendor Pricelist',
    'version' : '1.10',
    'summary': 'import the vendor pricelist',
    'description': """it used to import the vendor pricelist""",
    'author' : "HAK Technology",
     "license": "AGPL-3",
    'category': 'inventory',
    'website': '',
    'depends' : ['stock','purchase','product'],
    'data': [
        #'security/ir.model.access.csv',
         'data/data.xml',
         'wizard/import_vendor_pricelist.xml'
            ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
