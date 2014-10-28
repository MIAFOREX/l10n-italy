# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Davide Corio <davide.corio@lsweb.it>
#    Copyright (C) 2014 L.S. Advanced Software srl
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'DdT',
    'version': '1.0',
    'category': 'Localization/Italy',
    'summary': 'Documento di Trasporto',
    'description': """
Customizations needed to manage the italian DdT (delivery order).

Class, method and fields name are the same of l10n_it_sale, in order
to guarantee compatibility.

    """,
    'author': 'L.S. Advanced Software',
    'website': 'http://www.lsweb.it',
    'depends': ['account', 'base', 'stock', 'stock_account', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_data.xml',
        'views/account_view.xml',
        'views/partner_view.xml',
        'views/sale_view.xml',
        'views/stock_view.xml',
        'workflow/stock_ddt_workflow.xml'
    ],
    'installable': True,
    'active': False,
}