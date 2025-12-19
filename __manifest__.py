# -*- coding: utf-8 -*-
{
    'name': "ARCA - Carta de Porte",

    'summary': "Soporte de Cartas de porte via el WS de ARCA (ex AFIP)",

    'description': """
Soporte de Cartas de porte via el WS de ARCA (ex AFIP)
    """,

    'author': "Julio Santa Cruz",
    'website': "https://www.bartatech.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Localization/Argentina",
    'version': '17.0.0.4',

    # any module necessary for this one to work correctly
    'depends': ["base","l10n_ar_afipws","l10n_ar"],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml'
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    "maintainers": ["bartacruz"],
}

