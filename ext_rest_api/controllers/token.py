import json
import logging
import functools
import werkzeug.wrappers
import requests

from odoo import http
from odoo.addons.ext_rest_api.models.common import invalid_response, valid_response
from odoo.exceptions import AccessDenied, AccessError
from odoo.http import request
from odoo.addons.web.controllers.main import db_monodb, ensure_db, set_cookie_and_redirect, login_and_redirect

_logger = logging.getLogger(__name__)


class AccessToken(http.Controller):

    @http.route("/api/login/token_api_key", methods=["GET"], type="http", auth="none", csrf=False)
    def api_login_api_key(self, **post):

        headers = request.httprequest.headers
        api_key = headers.get("api_key")
        user_id = request.env["res.users.apikeys"]._check_credentials(scope="rpc", key=api_key)

        if not user_id:
            info = "authentication failed"
            error = "authentication failed"
            _logger.error(info)
            return invalid_response(401, error, info)
        user_obj = request.env['res.users'].sudo().browse(int(user_id))

        # Generate tokens
        access_token = request.env["api.access_token"].search([('api_key', '=', api_key)], order="id DESC", limit=1)
        token = access_token.token
        # Successful response:
        return werkzeug.wrappers.Response(
            status=200,
            content_type="application/json; charset=utf-8",
            headers=[("Cache-Control", "no-store"), ("Pragma", "no-cache")],
            response=json.dumps(
                {
                    "uid": user_id,
                    "session_id": request.session.sid if request.session.sid else False,
                    "user_context": request.session.get_context() if request.session.uid else {},
                    "company_id": user_obj.company_id.id if user_id else None,
                    "company_ids": user_obj.company_ids.ids if user_id else None,
                    "partner_id": user_obj.partner_id.id,
                    "access_token": token,
                    "company_name": user_obj.company_name,
                    "country": user_obj.country_id.name,
                    "contact_address": user_obj.contact_address,
                }
            ),
        )

    @http.route(["/api/auth/delete_token"], methods=["DELETE"], type="http", auth="none", csrf=False)
    def delete(self, **post):
        """Delete a given token"""
        token = request.env["api.access_token"]
        access_token = post.get("access_token")

        search_token = token.search([("token", "=", access_token)])
        if not access_token:
            error = "Access token is missing in the request header or invalid token was provided"
            return invalid_response(400, error)
        token.search([]).unlink()
        # Successful response:
        return valid_response([{"message": "access token %s successfully deleted" % (access_token,), "delete": True}])



