# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from odoo import api, fields, models


class ApiSettings(models.Model):
    _name = 'api.setting'

    model_id = fields.Many2one(comodel_name='ir.model', delegate=True, string='Api Model', ondelete='cascade',
                               required=True)
    read_html = fields.Html(string='[GET] Params', required=True)
    write_html = fields.Html(string='[POST] Params', required=True)
    unlink_html = fields.Html(string='[DELETE] Params', required=True)



