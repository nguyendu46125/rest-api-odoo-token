# -*- coding: utf-8 -*-
{
    'name': 'Rest API With Token',
    'version': "1.01",
    'author': "Du-IT",
    'category': 'Stock',
    'sequence': 41,
    'summary': 'Rest API With Token',
    'price': '59.0',
    'currency': 'USD',
    'description': "",
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/view_security.xml',
        'views/api_access_token.xml',
        # 'views/api_setting_views.xml',
        'views/templates.xml',
        'views/res_users.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'website': 'https://www.facebook.com/the.tam.944023',
    'license': 'LGPL-3',
    'images': ['static/description/gif.gif'],
}

