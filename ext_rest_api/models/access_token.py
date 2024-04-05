import hashlib
import logging
import os
import requests
from odoo.http import request
from datetime import datetime, timedelta
import random

from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

pass_key = {
    '1': ' ',
    '2': '!',
    '3': '"',
    '4': '#',
    '5': '$',
    '6': '%',
    '7': '&',
    '8': "'",
    '9': '(',
    '10': ')',
    '11': '*',
    '12': '+',
    '13': ',',
    '14': '-',
    '15': '.',
    '16': '/',
    '17': '0',
    '18': '1',
    '19': '2',
    '20': '3',
    '21': '4',
    '22': '5',
    '23': '6',
    '24': '7',
    '25': '8',
    '26': '9',
    '27': ':',
    '28': ';',
    '29': '<',
    '30': '=',
    '31': '>',
    '32': '?',
    '33': '@',
    '34': 'A',
    '35': 'B',
    '36': 'C',
    '37': 'D',
    '38': 'E',
    '39': 'F',
    '40': 'G',
    '41': 'H',
    '42': 'I',
    '43': 'J',
    '44': 'K',
    '45': 'L',
    '46': 'M',
    '47': 'N',
    '48': 'O',
    '49': 'P',
    '50': 'Q',
    '51': 'R',
    '52': 'S',
    '53': 'T',
    '54': 'U',
    '55': 'V',
    '56': 'W',
    '57': 'X',
    '58': 'Y',
    '59': 'Z',
    '60': '[',
    '61': '\\',
    '62': ']',
    '63': '^',
    '64': '_',
    '65': '`',
    '66': 'a',
    '67': 'b',
    '68': 'c',
    '69': 'd',
    '70': 'e',
    '71': 'f',
    '72': 'g',
    '73': 'h',
    '74': 'i',
    '75': 'j',
    '76': 'k',
    '77': 'l',
    '78': 'm',
    '79': 'n',
    '80': 'o',
    '81': 'p',
    '82': 'q',
    '83': 'r',
    '84': 's',
    '85': 't',
    '86': 'u',
    '87': 'v',
    '88': 'w',
    '89': 'x',
    '90': 'y',
    '91': 'z',
    '92': '{',
    '93': '|',
    '94': '}',
    '95': '~'
}


# we can make the expiry as a value taken from the
# token_expiry_date_in = "ext_rest_api_token.access_token_token_expiry_date_in"


def random_token(length=40, prefix="access_token"):
    # we can agree here how we can manage the token?
    rbytes = os.urandom(length)
    return "{}_{}".format(prefix, str(hashlib.sha1(rbytes).hexdigest()))


class APIAccessToken(models.Model):
    _name = "api.access_token"
    _description = "API Access Token"

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('done', 'Success'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, tracking=True, default='draft', stote=True)

    name = fields.Char("Name", default='API Access Token')
    token = fields.Char("Access Token", readonly=True)
    user_id = fields.Many2one("res.users", string="User", required=True)
    api_key = fields.Char(string="Api_key", required=True)
    db_name = fields.Char(string="DATABASE", readonly=True)
    pass_word = fields.Char(string=u"Password", required=True)
    login = fields.Char(string="User", readonly=True)
    link = fields.Char(string="link", readonly=True)

    @api.depends('day')
    def _compute_token_expiry_date(self):
        for line in self:
            if line.day:
                line.token_expiry_date = datetime.now() + timedelta(days=line.day)
            else:
                raise UserError(_("Điền thời gian sống cảu token!"))

    token_expiry_date = fields.Datetime(string="Token Expiry Date", readonly=True, compute="_compute_token_expiry_date",
                                        stote=True)
    scope = fields.Char(string="Scope")
    active = fields.Boolean(compute="_active", string="Active", default=False, readonly=True, stote=True)
    day = fields.Integer(string='Day', default=365)

    def _active(self):
        for line in self:
            if line.token_expiry_date:
                line.active = line.token_expiry_date > fields.Datetime.now()
                if line.token_expiry_date < fields.Datetime.now():
                    line.state = 'cancel'

    def random_string(self):
        characters_array = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        random_character = random.choice(characters_array)
        return random_character

    def ma_hoa(self, pass_code):
        if pass_code:
            char_array = ''
            for char in pass_code:
                for line in pass_key:
                    char_check = pass_key[line]
                    if char_check == char:
                        char_array += (self.random_string() + line)
            return char_array

    def giai_ma(self, pass_code):
        characters_array = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        char_find = ''
        if pass_code:
            char_array = []
            char_temp = ''
            for char in pass_code:
                if char not in characters_array:
                    char_temp += char
                else:
                    if char_temp == '':
                        continue
                    char_array.append(char_temp)
                    char_temp = ''
            if char_temp != '':
                char_array.append(char_temp)
            for line in char_array:
                if line == '':
                    continue
                else:
                    if line in pass_key:
                        key = pass_key.get(line)
                        char_find += key
        return char_find

    @api.model
    def create(self, vals):
        if 'pass_word' in vals:
            pass_new = self.ma_hoa(vals.get('pass_word'))
            vals.update({'pass_word': pass_new})
        for key in self:
            if vals.get('api_key') == key.api_key:
                raise UserError(_("API_KEY đã tồn tại???"))
        return super(APIAccessToken, self).create(vals)

    def write(self, vals):
        for key in self:
            if vals.get('api_key') == key.api_key:
                raise UserError(_("API_KEY đã tồn tại???"))
        if 'pass_word' in vals:
            pass_new = self.ma_hoa(vals.get('pass_word'))
            vals.update({'pass_word': pass_new})
        return super(APIAccessToken, self).write(vals)

    def create_token(self):
        headers = request.httprequest.headers
        link = request.httprequest.environ.get("HTTP_HOST")
        db_name = request.env.cr.dbname
        api_key = self.api_key
        uid = self.user_id.id

        user_id = request.env["res.users.apikeys"]._check_credentials(scope="rpc", key=api_key)
        if not user_id:
            raise UserError(_("Check lại API_KEY trong USER/My Profile/Account Security!!!"))
        else:
            if user_id != uid:
                raise UserError(_("API_KEY không trùng vs user!!!"))
        vals = {
            "token": random_token(),
            "link": link,
            "login": self.user_id.login,
            "db_name": db_name,
            "state": 'done',
            "active": True,
        }
        self.write(vals)

    def find_or_create_token(self, user_id=None, create=False):
        if not user_id:
            user_id = self.env.user.id

        access_token = self.env["api.access_token"].sudo().search([("user_id", "=", user_id)], order="id DESC")
        if len(access_token) == 1:
            access_token = access_token[0]
            if access_token.has_expired() or not access_token.active:
                self.env["api.access_token"].sudo().search([]).unlink()
                access_token = None
            else:
                return access_token.token
        else:
            self.env["api.access_token"].sudo().search([]).unlink()
            access_token = None
        if not access_token and create:
            token_expiry_date = datetime.now() + timedelta(days=7)
            vals = {
                "user_id": user_id,
                "scope": "userinfo",
                "token_expiry_date": token_expiry_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                "token": random_token(),
            }
            access_token = self.env["api.access_token"].sudo().create(vals)
        return access_token.token

    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.

        :param scopes: An iterable containing the scopes to check or None
        """
        self.ensure_one()
        return not self.has_expired() and self._allow_scopes(scopes)

    def has_expired(self):
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.token_expiry_date)

    def _allow_scopes(self, scopes):
        self.ensure_one()
        if not scopes:
            return True

        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)


class Users(models.Model):
    _inherit = "res.users"

    def sum_numbers(self, x, y):
        return x + y

    token_ids = fields.One2many("api.access_token", "user_id", string="Access Tokens")
