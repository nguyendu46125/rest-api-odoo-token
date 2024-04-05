import logging
import functools

from odoo import http
from odoo.addons.ext_rest_api.models.common import invalid_response, valid_response
from odoo.http import request
import re

_logger = logging.getLogger(__name__)


def convert_tv(s):
    patterns = {
        '[àáảãạăắằẵặẳâầấậẫẩ]': 'a',
        '[đ]': 'd',
        '[èéẻẽẹêềếểễệ]': 'e',
        '[ìíỉĩị]': 'i',
        '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
        '[ùúủũụưừứửữự]': 'u',
        '[ỳýỷỹỵ]': 'y',
        '[ÀÁẢÃẠĂẮẰẴẶẲÂẦẤẬẪẨ]': 'a',
        '[Đ]': 'd',
        '[ÈÉẺẼẸÊỀẾỂỄỆ]': 'e',
        '[ÌÍỈĨỊ]': 'I',
        '[ÒÓỎÕỌÔỐỒỔỖỘƠỜỚỞỠỢ]': 'o',
        '[ÙÚỦŨỤƯỪỨỬỮỰ]': 'u',
        '[ỲÝỶỸỴ]': 'y',
        '[ ]': '',
        '[\n]': '',
        '[\t]': '',
        '[,]': '',
    }
    if s:
        for regex, replace in patterns.items():
            s = re.sub(regex, replace, s)
            # deal with upper case
            s = re.sub(regex.upper(), replace.upper(), s)
        return s


def validate_token(func):
    """."""

    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        access_token_data = request.env["api.access_token"].sudo().search([("token", "=", access_token)],
                                                                          order="id DESC", limit=1)

        if not access_token_data.active:
            return invalid_response("access_token", "token not active!!!", 401)

        if access_token_data.state != "done":
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        db = access_token_data.db_name
        username = access_token_data.login
        password = access_token_data.giai_ma(access_token_data.pass_word)

        login_search = request.env["res.users"].sudo().search_read(fields=['name'], domain=[("login", "=", username)],
                                                                   limit=1)
        if not login_search:
            return invalid_response("access_token", "User token not found", 401)
        try:
            request.session.authenticate(db, username, password)
        except Exception as e:
            return invalid_response("access_token", "Wrong Password!!!", 401)
        return func(self, *args, **kwargs)

    return wrap

