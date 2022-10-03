# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime

import jwt
import requests

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.user_login_logout import get_tokens


class SrvTokenManager(metaclass=MetaService):
    def __init__(self):
        user_config = UserConfig()
        has_user = user_config.config.has_section("USER")
        has_access_token = user_config.config.has_option("USER", "access_token")
        has_refresh_token = user_config.config.has_option("USER", "refresh_token")
        if has_user and has_access_token and has_refresh_token:
            self.config = user_config
        else:
            raise(Exception('Login session not found, please login first.'))

    def update_token(self, access_token, refresh_token):
        self.config.access_token = access_token
        self.config.refresh_token = refresh_token
        self.config.save()

    def get_token(self):
        return self.config.access_token, self.config.refresh_token

    def decode_access_token(self):
        tokens = self.get_token()
        return jwt.decode(tokens[0], verify=False)

    def decode_refresh_token(self):
        tokens = self.get_token()
        return jwt.decode(tokens[1], verify=False)

    def check_valid(self, required_azp):
        '''
        check token validation
        0: valid
        1: need refresh
        2: need login again
        '''
        decoded_access_token = self.decode_access_token()
        expiry_at = datetime.datetime.utcfromtimestamp(decoded_access_token['exp'])
        now = datetime.datetime.utcnow()
        diff = int((expiry_at - now).seconds)

        # TODO: check why here will need enforce the token refresh when
        # azp is not `kong``
        azp_token_condition = decoded_access_token['azp'] != required_azp
        if azp_token_condition:
            return 3
        if expiry_at <= now:
            return 2
        if diff <= AppConfig.Env.token_warn_need_refresh:
            return 1
        return 0

    def request_default_tokens(self):
        url = AppConfig.Connections.url_refresh_token
        payload = {
            'refreshtoken': self.config.refresh_token
        }
        headers = {
            'Authorization': 'Bearer ' + self.config.access_token,
            'Content-Type': 'application/json'
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            self.update_token(response.json()['result']['access_token'], response.json()['result']['refresh_token'])
        else:
            SrvErrorHandler.default_handle(response.content)
        return response.json()

    def request_harbor_tokens(self):
        url = AppConfig.Connections.url_keycloak
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.config.refresh_token,
            'client_id': 'harbor',
            'client_secret': AppConfig.Env.harbor_client_secret
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.post(url, data=payload, headers=headers, verify=False)
        if response.status_code == 200:
            self.update_token(response.json()['access_token'], response.json()['refresh_token'])
        else:
            SrvErrorHandler.default_handle(response.content)
        return response.json()

    def refresh(self, azp):
        if not azp or azp == 'kong':
            self.request_default_tokens()
        if azp == 'harbor':
            self.request_harbor_tokens()

    def change_token(self, required_azp):
        tokens = get_tokens(self.config.username, self.config.password, required_azp)
        self.update_token(tokens[0], tokens[1])
