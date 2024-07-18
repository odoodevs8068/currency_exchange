
{
    'name': 'Sales/Invoice Total Amount Exchange',
    'version': '1.2',
    'summary': '',
    'author': "JD DEVS",
    'sequence': 10,
    'depends': ['base', 'sale', 'account', 'product'],
    'data': [
        'views/views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            "currency_exchange_rate/static/src/js/tax_total_new_widget.js",
        ],

        'web.assets_qweb': [
            "currency_exchange_rate/static/src/xml/total_tax_json_widget_template.xml",
            "currency_exchange_rate/static/src/xml/tax_total_tmpl_inherit.xml",
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
