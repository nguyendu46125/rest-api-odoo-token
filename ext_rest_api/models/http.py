from odoo import http
from odoo.http import request
from odoo.http import WebRequest
import json
# -*- coding: utf-8 -*-
#----------------------------------------------------------
# OpenERP HTTP layer
#----------------------------------------------------------
import ast
import cgi
import collections
import contextlib
import functools
import hashlib
import hmac
import inspect
import logging
import mimetypes
import os
import pprint
import odoo
import re
import sys
import threading
import time
import traceback
import warnings
from os.path import join as opj
from zlib import adler32

import babel.core
from datetime import datetime
import passlib.utils
import psycopg2
import json
import werkzeug.datastructures
import werkzeug.exceptions
import werkzeug.local
import werkzeug.routing
import werkzeug.wrappers
from werkzeug import urls
from werkzeug.wsgi import wrap_file
try:
    from werkzeug.middleware.shared_data import SharedDataMiddleware
except ImportError:
    from werkzeug.wsgi import SharedDataMiddleware

try:
    import psutil
except ImportError:
    psutil = None

_logger = logging.getLogger(__name__)
rpc_request = logging.getLogger(__name__ + '.rpc.request')
rpc_response = logging.getLogger(__name__ + '.rpc.response')

class Response(werkzeug.wrappers.Response):

    default_mimetype = 'text/html'
    def __init__(self, *args, **kw):
        template = kw.pop('template', None)
        qcontext = kw.pop('qcontext', None)
        uid = kw.pop('uid', None)
        super(Response, self).__init__(*args, **kw)
        self.set_default(template, qcontext, uid)

    def set_default(self, template=None, qcontext=None, uid=None):
        self.template = template
        self.qcontext = qcontext or dict()
        self.qcontext['response_template'] = self.template
        self.uid = uid
        # Support for Cross-Origin Resource Sharing
        if request.endpoint and 'cors' in request.endpoint.routing:
            self.headers.set('Access-Control-Allow-Origin', request.endpoint.routing['cors'])
            methods = 'GET, POST'
            if request.endpoint.routing['type'] == 'json':
                methods = 'POST'
            elif request.endpoint.routing.get('methods'):
                methods = ', '.join(request.endpoint.routing['methods'])
            self.headers.set('Access-Control-Allow-Methods', methods)

    @property
    def is_qweb(self):
        return self.template is not None

    def render(self):
        """ Renders the Response's template, returns the result
        """
        env = request.env(user=self.uid or request.uid or odoo.SUPERUSER_ID)
        self.qcontext['request'] = request
        return env["ir.ui.view"]._render_template(self.template, self.qcontext)

    def flatten(self):
        """ Forces the rendering of the response's template, sets the result
        as response body and unsets :attr:`.template`
        """
        if self.template:
            self.response.append(self.render())
            self.template = None





# # Ghi đè hàm check_session
# def custom_check_session(session, env):
#
#     self = env['res.users'].browse(session.uid)
#     expected = self._compute_session_token(session.sid)
#     if expected:
#         try:
#             if odoo.tools.misc.consteq(expected, session.session_token):
#                 return True
#         except Exception:
#             # self._invalidate_session_cache()
#             return False
#     self._invalidate_session_cache()
#     result = odoo_security.check_session(session, env)
#     return False
#
# odoo_security.check_session = custom_check_session

# class IrHttp(models.AbstractModel):
#     _inherit = "ir.http"
#
#     @classmethod
#     def _auth_method_api_key(cls):
#         api_key = request.httprequest.headers.get("api_key")
#         if not api_key:
#             raise BadRequest("Authorization header with API key missing")
#
#         user_id = request.env["res.users.apikeys"]._check_credentials(
#             scope="rpc", key=api_key
#         )
#         if not user_id:
#             raise BadRequest("API key invalid")
#
#         request.uid = user_id
