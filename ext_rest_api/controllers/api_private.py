import logging
import functools

from odoo import http
from odoo.addons.ext_rest_api.models.common import invalid_response, valid_response
from odoo.addons.ext_rest_api.controllers.validate_token import validate_token, convert_tv
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import date_utils
import json
import re

_logger = logging.getLogger(__name__)


class ApiDu(http.Controller):
    """."""

    def __init__(self):
        self._model = "ir.model"

    # access_token_30b55fed1f2a2d3976a06ccf85ae02a8cdb2dd39

    # ==============================API-WEB===================================
    @validate_token
    @http.route('/api/v1/private_web/stock_quant/product', methods=["GET"], type="http", auth="none", csrf=False)
    def get_private_stock_quant_product_id_in_web(self, variant_id=None, tmpl_id=None):
        cr = request.env.cr
        product_id = None
        if variant_id:
            try:
                product_id = int(variant_id)
            except ValueError:
                return valid_response({'error': 'ID Product not Integer!!!'})
        if tmpl_id:
            try:
                product_tmpl_id = int(tmpl_id)
                cr.execute("""
                    SELECT id, product_tmpl_id
                    FROM product_product
                    WHERE product_tmpl_id = %d """ % product_tmpl_id)
                product = cr.dictfetchall()
                product_id = product[0].get('id')
            except ValueError:
                return valid_response({'error': 'ID Product not Integer!!!'})
        if product_id:
            cr.execute("""
                SELECT id
                FROM product_product
                WHERE id = %d """ % product_id)
            data_product = cr.dictfetchone()
            if not data_product:
                return valid_response({'error': 'Product_id not found in ERP !!!'})
        else:
            return valid_response({'error': 'Where product_id!!!'})
        cr.execute("""
            SELECT id, location_id, quantity
            FROM stock_quant
            WHERE product_id = %s AND location_id not in (4, 2, 5)""", (product_id,))
        quants_total = cr.dictfetchall()
        product_data = []
        for quant_line in quants_total:
            product_data.append({
                "location_id": quant_line.get('id'),
                "amount": quant_line.get('quantity'),
            })
        data = {
            'stocks': product_data,
        }
        return valid_response(data)
    # ==============================API-WEB===================================

    # api web get stock_quant by product_id
    @validate_token
    @http.route('/api/v1/private_web/stock_quant/data', methods=["GET"], type="http", auth="none", csrf=False)
    def get_private_stock_quant_body_in_web(self, **kwargs):
        cr = request.env.cr
        try:
            data_body = json.loads(request.httprequest.data)
            if not data_body:
                return valid_response({'error': 'Body not found!!!'})
        except ValueError:
            return valid_response({'error': 'ID Product not Integer!!!'})
        params = data_body.get('params')

        orders = params.get('orders')
        location = params.get('location')
        id_pros = ()
        for product_line in orders:
            product_id = product_line.get('product_id')
            product_qty = product_line.get('qty')

        domain = [('location_id', 'not in', [4, 2, 5])]
        quants_total = []
        if id_pros:
            domain = [('location_id', 'not in', [4, 2, 5]), ('product_id', 'in', id_pros)]
            cr.execute("""
                SELECT id
                FROM stock_quant
                WHERE product_id in %s AND location_id not in (4, 2, 5)""", (id_pros,))
            quants_total = cr.dictfetchall()
        else:
            cr.execute("""SELECT id FROM stock_quant WHERE location_id not in (4, 2, 5)""")
            quants_total = cr.dictfetchall()
        fields = ['id', 'product_id', 'location_id', 'quantity']
        # order = 'name ASC'
        quants_all = request.env['stock.quant'].sudo().search_read(domain=domain, fields=fields, offset=0)
        if not quants_all:
            return valid_response({'error': 'No DATA'})

        total = len(quants_total)
        # Chuyển đổi dữ liệu sản phẩm thành định dạng JSON
        product_data = []
        for quant_line in quants_all:
            product_id = quant_line['product_id'][0]
            product_name = quant_line['product_id'][1]
            cr.execute("""
                SELECT id, default_code, product_tmpl_id
                FROM product_product
                WHERE id = %s """ % product_id)
            data_product = cr.dictfetchone()
            sku = data_product.get('default_code')

            product_tmpl_id = data_product.get('product_tmpl_id')
            cr.execute("""
                SELECT id, default_code, list_price
                FROM product_template
                WHERE id = %d """ % product_tmpl_id)
            data_product_tmpl = cr.dictfetchone()
            if not sku:
                sku = data_product_tmpl.get('default_code')
            price = data_product_tmpl.get('list_price')

            location_id = quant_line['location_id'][0]
            # if location_id == 4:
            #     continue
            cr.execute("""
                SELECT id, name, complete_name, type, warehouse_id
                FROM stock_location
                WHERE id = %d """ % location_id)
            data_location = cr.dictfetchone()
            store_code = data_location.get('complete_name')
            warehouse_id = data_location.get('warehouse_id')
            location_type = data_location.get('type')

            cr.execute("""
                SELECT name
                FROM stock_warehouse
                WHERE id = %d """ % warehouse_id)
            store_name = cr.dictfetchone().get('name')

            product_data.append({
                "id": quant_line.get('id'),
                "sku": sku,
                "product_name": product_name,
                # "variant": attributes_line,
                "store_name": store_name,
                "location_type": location_type,
                "amount": quant_line.get('quantity'),
                "price": price,
            })
        data = {
            'data': product_data,
            "total": total,
        }
        return valid_response(data)

    # =================================================================

    # api get stock_location
    @validate_token
    @http.route('/api/v1/private_endpoint/stock_location', methods=["GET"], type="http", auth="none", csrf=False)
    def get_location_private(self):

        try:
            limit = 1000
            offset = 0
            domain = [('name', '=', 'Stock')]
            fields = ['id', 'complete_name', 'type']

            location_all = request.env['stock.location'].sudo().search_read(domain=domain, fields=fields, offset=offset,
                                                                            limit=limit, order='name ASC')
            location_data = []
            for location in location_all:
                complete_name = location.get('complete_name')
                location_type = location.get('type')

                location_data.append({
                    "id": location.get('id'),
                    "location_name": complete_name,
                    "location_type": location_type,
                })
            data = {
                'location': location_data,
            }
            return valid_response(data)
        except AccessError as e:
            return valid_response({'error': 'No DATA'})

    # api mobile get stock_quant
    @validate_token
    @http.route('/api/v1/private_mobile/stock_quant', methods=["GET"], type="http", auth="none", csrf=False)
    def get_product_private(self, page=1, limit=10, types=None, search=None):
        cr = request.env.cr

        try:
            page = int(page)
            limit = int(limit)
            types = str(types)
            search_sku = str(search)
        except ValueError:
            return json.dumps({'error': 'Invalid page or page_size parameter'})

        id_pros = ()
        if types == 'sku':
            if search:
                product_pro = request.env['product.product'].sudo().search_read(
                    domain=[('default_code', 'ilike', search_sku)],
                    fields=['id'])
                if product_pro:
                    values_id = (d['id'] for d in product_pro)
                    id_pros = tuple(values_id)
                else:
                    return valid_response({'error': 'SKU not found'})

        elif types == 'name':
            if search:
                product_pro = request.env['product.product'].sudo().search_read(fields=['id', 'name'])
                if product_pro:
                    search_con = convert_tv(search).lower()
                    for product_tv in product_pro:
                        pro_con = convert_tv(product_tv.get('name')).lower()
                        if search_con in pro_con:
                            id_pros += (product_tv.get('id'),)
                else:
                    return valid_response({'error': 'Name not found'})

        elif types == 'barcode':
            if search:
                cr.execute("""
                    SELECT id, default_code, product_tmpl_id
                    FROM product_product
                    WHERE barcode = '%s' """ % search)
                product_pro = cr.dictfetchone()
                if product_pro:
                    id_pros = (product_pro.get('id'),)
                else:
                    return valid_response({'error': 'Barcode not found'})

        # Tính toán offset và limit để lấy sản phẩm theo trang
        offset = (page - 1) * limit

        # Truy vấn dữ liệu sản phẩm từ Odoo
        domain = [('location_id', 'not in', [4, 2, 5])]
        quants_total = []
        if id_pros:
            domain = [('location_id', 'not in', [4, 2, 5]), ('product_id', 'in', id_pros)]
            cr.execute("""
                SELECT id
                FROM stock_quant
                WHERE product_id in %s AND location_id not in (4, 2, 5)""", (id_pros,))
            quants_total = cr.dictfetchall()
        else:
            cr.execute("""SELECT id FROM stock_quant WHERE location_id not in (4, 2, 5)""")
            quants_total = cr.dictfetchall()
        fields = ['id', 'product_id', 'location_id', 'quantity']
        # order = 'name ASC'
        quants_all = request.env['stock.quant'].sudo().search_read(domain=domain, fields=fields, offset=offset,
                                                                   limit=limit)
        if not quants_all:
            return valid_response({'error': 'No DATA'})

        total = len(quants_total)
        page_total = total // limit
        # Chuyển đổi dữ liệu sản phẩm thành định dạng JSON
        product_data = []
        for quant_line in quants_all:
            product_id = quant_line['product_id'][0]
            product_name = quant_line['product_id'][1]
            cr.execute("""
                SELECT id, default_code, product_tmpl_id
                FROM product_product
                WHERE id = %s """ % product_id)
            data_product = cr.dictfetchone()
            sku = data_product.get('default_code')

            product_tmpl_id = data_product.get('product_tmpl_id')
            cr.execute("""
                SELECT id, default_code, list_price
                FROM product_template
                WHERE id = %d """ % product_tmpl_id)
            data_product_tmpl = cr.dictfetchone()
            if not sku:
                sku = data_product_tmpl.get('default_code')
            price = data_product_tmpl.get('list_price')

            location_id = quant_line['location_id'][0]
            # if location_id == 4:
            #     continue
            cr.execute("""
                SELECT id, name, complete_name, type
                FROM stock_location
                WHERE id = %d """ % location_id)
            data_location = cr.dictfetchone()
            store_name = data_location.get('complete_name')
            address = data_location.get('name')
            location_type = data_location.get('type')

            product_data.append({
                "id": quant_line.get('id'),
                "sku": sku,
                "product_name": product_name,
                "store_name": store_name,
                "location_type": location_type,
                "amount": quant_line.get('quantity'),
                "price": price,
                "discountPrice": 0.0,
                "address": address,
            })
        data = {
            'data': product_data,
            "total": total,
            "page": page,
            "limit": limit,
            "pageTotal": total // limit,
        }
        # Trả về dữ liệu JSON
        # return json.dumps({'page_products': data})
        return valid_response(data)

    # Api POST
    # Api DELETE
    @validate_token
    @http.route("/api/api_delete/<string:model_name>", methods=["DELETE"], type="http", auth="none", csrf=False)
    def delete(self, **post):
        error = "Waiting DU-IT to develop"
        return invalid_response(400, error)
