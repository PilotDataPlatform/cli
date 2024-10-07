# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import time

import jwt
import requests

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.output_manager.error_handler import SrvErrorHandler


class SrvTokenManager(metaclass=MetaService):
    def __init__(self):
        user_config = UserConfig()
        has_user = user_config.config.has_section('USER')
        has_access_token = user_config.config.has_option('USER', 'access_token')
        has_refresh_token = user_config.config.has_option('USER', 'refresh_token')
        if has_user and has_access_token and has_refresh_token:
            self.config = user_config
        else:
            raise (Exception('Login session not found, please login first.'))

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
        """
        check token validation
        0: valid
        1: need refresh
        2: need login again
        """
        decoded_access_token = self.decode_access_token()
        expiry_at = int(decoded_access_token['exp'])
        now = time.time()
        diff = expiry_at - now

        # TODO: check why here will need enforce the token refresh when
        # azp is not `kong``
        # ``kong`` is hardcoded in the decorator definition as default value.
        azp_token_condition = decoded_access_token['azp'] not in [required_azp, AppConfig.Env.keycloak_device_client_id]

        if azp_token_condition or expiry_at <= now:
            return 2
        # print(expiry_at, now)
        # print(diff, AppConfig.Env.token_warn_need_refresh)
        if diff <= AppConfig.Env.token_warn_need_refresh:
            return 1
        return 0

    def refresh(self, azp: str):
        url = AppConfig.Connections.url_keycloak_token
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.config.refresh_token,
            'client_id': azp,
        }

        if azp == 'harbor':
            payload.update({'client_id': AppConfig.Env.harbor_client_secret})

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            self.update_token(response.json()['access_token'], response.json()['refresh_token'])
        else:
            SrvErrorHandler.default_handle(response.content)
        return response.json()
