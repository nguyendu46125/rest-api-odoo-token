import logging
import functools
from odoo import http
from odoo.addons.ext_rest_api.models.common import invalid_response, valid_response
from odoo.tools import date_utils
from odoo.addons.ext_rest_api.controllers.validate_token import validate_token, convert_tv
from odoo.http import request, WebRequest, Response
import datetime
import werkzeug.wrappers
import json
import odoo
from datetime import datetime

_logger = logging.getLogger(__name__)


class PublicApiController(http.Controller):

    @http.route('/api/v2/public_endpoint/stock_quant', auth='public', methods=['GET'], type='http')
    def get_product_public(self, page=1, limit=10, types=None, search=None):
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
                SELECT id, name, complete_name
                FROM stock_location
                WHERE id = %d """ % location_id)
            data_location = cr.dictfetchone()
            store_name = data_location.get('complete_name')
            address = data_location.get('name')

            product_data.append({
                "id": quant_line.get('id'),
                "sku": sku,
                "product_name": product_name,
                "store_name": store_name,
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

    @http.route('/api/v1/public_web/stock_quant/product', methods=["GET"], type="http", auth="public", csrf=False)
    def get_private_stock_quant_product_id_in_web(self, id=None):

        cr = request.env.cr
        try:
            product_id = int(id)
        except ValueError:
            return valid_response({'error': 'ID Product not Integer!!!'})

        id_pros = ()
        attributes_line = []
        if product_id:
            product_pro = request.env['product.product'].sudo().search_read(
                domain=[('id', '=', product_id)],
                fields=['id', 'product_template_attribute_value_ids'])
            if product_pro[0]['product_template_attribute_value_ids']:
                for attribute_id in product_pro[0]['product_template_attribute_value_ids']:
                    cr.execute("""
                        SELECT id,product_attribute_value_id,attribute_id FROM product_template_attribute_value
                        WHERE id = %d """ % attribute_id)
                    values = cr.dictfetchone()
                    product_attribute_value_id = values.get('product_attribute_value_id')
                    attribute_value_id = values.get('attribute_id')

                    cr.execute("""
                        SELECT name FROM product_attribute
                        WHERE id = %d """ % attribute_value_id)
                    attribute = cr.dictfetchone().get('name')
                    cr.execute("""
                        SELECT name FROM product_attribute_value
                        WHERE id = %d """ % product_attribute_value_id)
                    attribute_value = cr.dictfetchone().get('name')
                    attributes_line.append({attribute: attribute_value})

            if product_pro:
                values_id = (d['id'] for d in product_pro)
                id_pros = tuple(values_id)
            else:
                return valid_response({'error': 'sku not found in stock!!!'})
        else:
            return valid_response({'error': 'You have not entered a sku!!!'})
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
        quants_all = request.env['stock.quant'].sudo().search_read(domain=domain, fields=fields, offset=0)
        if not quants_all:
            return valid_response({'error': 'No DATA'})

        total = len(quants_total)
        # Chuyển đổi dữ liệu sản phẩm thành định dạng JSON
        product_data = []
        # count = 0
        for quant_line in quants_all:
            # count += 1
            # if count < 62:
            # continue
            product_id_in_quant = quant_line['product_id'][0]
            product_name = quant_line['product_id'][1]
            cr.execute("""
                SELECT id, default_code, product_tmpl_id
                FROM product_product
                WHERE id = %s """ % product_id_in_quant)
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

            if warehouse_id:
                cr.execute("""
                    SELECT name
                    FROM stock_warehouse
                    WHERE id = %d """ % warehouse_id)
                store_name = cr.dictfetchone().get('name')
            else:
                continue

            product_data.append({
                "id": quant_line.get('id'),
                "store_name": store_name,
                "location_type": location_type,
                "amount": quant_line.get('quantity'),
                "price": price,
            })
        data = {
            "total": total,
            "sku": sku,
            "product_name": product_name,
            'attributes': attributes_line,
            'stocks': product_data,
        }
        return valid_response(data)

    @http.route('/api/v2/private_web/api_vtb_qr', methods=["POST"], type="json", auth="public", csrf=False)
    def get_api_vtb_qr(self, **post):

        error_detail = {}
        try:
            headers = {'Content-Type': 'application/json'}
            data = json.loads(request.httprequest.data)

            # body = requests
            data_1 = request.jsonrequest
            return werkzeug.wrappers.Response(
                status=200, content_type="application/json; charset=utf-8",
                response=json.dumps(data),
            )
            # if not body:
            #     return valid_response({'error': 'Body is required!!!'})
            check = 'ci7J+pN378zwfV/foY87tKyvpBpmcsE4nyK8ARq86JBviUImZzLUplvf2bOrF2smr/tk7wuw2XuF9XH1qzsmgaqYrgRkh9wHCImONHJEak9gVX0shlbpLhZweHv3pzm3Pf6WFaPow5tL3U2Vcfe1D8MH38cKc9mfgp68SIGNB+IpGCf0NzHWTSwNQ2lYfvFRiLR45Hhnmu0cKggjgvtkhJSxK37mKJF048WYWYSFPjloFn8sr0WSUZg2bcVxRR8Yo9XX0Z6ETxJnv2HuSM6QdwlFzHZeaizRsqyQ2qlkYq0s3jstGDvLpKKjQjQuFl1fkKG3lNPjCABRN1VuCfxCrQ=='
            # if signature != check:
            #     return Response(json.dumps({
            #         "data": data_notification,
            #         "success": True,
            #         "message": "Success"
            #     }), headers=headers)
            data_notification = request.env['pos.qr.payment'].bus_confirm_qr_payment(data)

            mime = 'application/json'
            body = json.dumps(data_notification, default=date_utils.json_default)
            return Response(mime)

        except Exception as e:
            return Response(json.dumps({
                "success": False,
                "data": error_detail,
                "error_message": f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"
            }), 500)
