# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import time

import jwt
from httpx import HTTPStatusError

from app.configs.app_config import AppConfig
from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.clients.base_client import BaseClient
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.user_login_logout import login_using_api_key


class SrvTokenManager(BaseClient, metaclass=MetaService):
    def __init__(self):
        super().__init__(AppConfig.Connections.url_keycloak_token, 10)
        user_config = UserConfig()
        if user_config.is_logged_in():
            self.config = user_config
        else:
            raise Exception('Login session not found, please login first.')

    def update_token(self, access_token, refresh_token):
        self.config.access_token = access_token
        self.config.refresh_token = refresh_token
        self.config.save()

    def get_token(self):
        return self.config.access_token, self.config.refresh_token

    def decode_access_token(self):
        tokens = self.get_token()
        return jwt.decode(tokens[0], options={'verify_signature': False}, algorithms=['RS256'])

    def decode_refresh_token(self):
        tokens = self.get_token()
        return jwt.decode(tokens[1], options={'verify_signature': False}, algorithms=['RS256'])

    def is_api_key(self) -> bool:
        token = self.decode_access_token()
        audience = token['aud']
        if isinstance(audience, list):
            return ConfigClass.keycloak_api_key_audience.issubset(set(audience))
        return False

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

        azp_token_condition = decoded_access_token['azp'] not in [
            required_azp,
            ConfigClass.keycloak_device_client_id,
        ]

        if azp_token_condition or expiry_at <= now:
            # check if refresh token and apikey is available
            decoded_refresh_token = self.decode_refresh_token()
            expiry_at = int(decoded_refresh_token['exp'])
            if expiry_at <= now:
                is_valid = login_using_api_key(self.config.api_key)
                if not is_valid:
                    SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TOKEN, if_exit=True)
                    return 2
                return 1
            return 1

        if diff <= AppConfig.Env.token_warn_need_refresh:
            return 1
        return 0

    def refresh(self, azp: str) -> None:
        # url = AppConfig.Connections.url_keycloak_token
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.config.refresh_token,
            'client_id': azp,
        }

        if azp == 'harbor':
            payload.update({'client_id': ConfigClass.harbor_client_secret})

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.endpoint, url = AppConfig.Connections.url_keycloak_token.rsplit('/', 1)
        try:
            response = self._post(url, data=payload, headers=headers)
            res = response.json()
            self.update_token(res.get('access_token'), res.get('refresh_token'))
        except HTTPStatusError as e:
            response = e.response
            # 401 is invalid token and 400 is session inactive we do refresh
            if response.status_code in [400, 401, 500]:
                is_valid = login_using_api_key(self.config.api_key)
                if not is_valid:
                    SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TOKEN, if_exit=True)
            else:
                SrvErrorHandler.default_handle(response.content)
