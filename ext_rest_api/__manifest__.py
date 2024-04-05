# -*- coding: utf-8 -*-
{
    'name': "REST API",

    'summary': """
        Xedap.vn""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Du-IT",
    'website': "http://xedap.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
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
}
