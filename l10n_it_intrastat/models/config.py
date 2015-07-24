# -*- coding: utf-8 -*-
##############################################################################
#    
#    Author: Alessandro Camilli (a.camilli@openforce.it)
#    Copyright (C) 2014
#    Openforce di Camilli Alessandro (www.openforce.it)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api


class res_company(models.Model):
    _inherit = 'res.company'
    
    intrastat_uom_kg_id = fields.Many2one(
        'product.uom', string="Unit of measure for Kg",
        )
    intrastat_ua_code = fields.Char(string="User ID (UA Code)", size=4)


class account_config_settings(models.TransientModel):
    _inherit = 'account.config.settings'

    intrastat_uom_kg_id = fields.Many2one(
        'product.uom', string="Unit of measure for Kg",
        related='company_id.intrastat_uom_kg_id',
        )
    intrastat_ua_code = fields.Char(string="User ID (UA Code)", size=4,
        related='company_id.intrastat_ua_code'
        )