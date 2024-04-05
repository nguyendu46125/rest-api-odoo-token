# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, timedelta
import requests

class Products(models.Model):
    _inherit = 'product.product'

    def call_api_create_product_website(self, url):
        if not url:
            url = 'active.vn'
        product_tmpl_obj = self.env['product.template']

        data_post = {
            "items": [
                {
                    "seoTitle": "seo tieu de",
                    "seoDescription": "seo description",
                    "seoKeyword": "keyword",
                    "seoImage": "Image URL",
                    "productId": "string",
                    "brand": "string",
                    "title": "football",
                    "alias": "football",
                    "description": "",
                    "rentPrices": [
                        {
                            "type": "hour",
                            "price": 0
                        }
                    ],
                    "shortDescription": "Image URL",
                    "gallery": [],
                    "images": [],
                    "thumbnail": "",
                    "accompanyingGifts": "accompanyingGifts",
                    "specifications": "specifications",
                    "sku": "Abc-0123",
                    "categories": [
                        "string"
                    ],
                    "productTypes": [
                        "string"
                    ],
                    "collections": [
                        "string"
                    ],
                    "attributeItems": [
                        "string"
                    ],
                    "isPrimary": True,
                    "price": 0,
                    "sellPrice": 0,
                    "stock": 1,
                    "platform": [
                        None
                    ],
                    "isGift": True,
                    "isRental": True,
                    "variants": [
                        "string"
                    ]
                }
            ]
        }

        main_url = "https://" + url + "/admin-api/external/product"
        base_headers = {
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(main_url, json=data_post, headers=base_headers)

            if response.status_code == 200:
                result = response.json()
                if result.get('status').get('code') == '00':
                    request_id = result.get('requestId')
                    data_qr = result.get('qrData')
                    return {
                        'requestId': request_id,
                        'qrData': data_qr,
                    }
            else:
                print(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
            return '01'
