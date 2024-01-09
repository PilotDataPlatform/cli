# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import time

import jwt
import requests

from app.configs.app_config import AppConfig
from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig
from app.models.enums import LoginMethod
from app.models.service_meta_class import MetaService
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.user_login_logout import exchange_api_key


class SrvTokenManager(metaclass=MetaService):
    def __init__(self):
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
        return jwt.decode(tokens[0], verify=False)

    def decode_refresh_token(self):
        tokens = self.get_token()
        return jwt.decode(tokens[1], verify=False)

    def is_api_key(self) -> bool:
        token = self.decode_access_token()
        audience = token['aud']
        if isinstance(audience, str):
            audience = [audience]
        return ConfigClass.keycloak_api_key_audience.issubset(set(audience))

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

        if not self.is_api_key():
            # TODO: check why here will need enforce the token refresh when
            # azp is not `kong``
            # ``kong`` is hardcoded in the decorator definition as default value.
            azp_token_condition = decoded_access_token['azp'] not in [
                required_azp,
                ConfigClass.keycloak_device_client_id,
            ]

            if azp_token_condition or expiry_at <= now:
                return 2

        if diff <= AppConfig.Env.token_warn_need_refresh:
            return 1
        return 0

    def refresh(self, azp: str) -> None:
        if self.is_api_key():
            return self.refresh_api_key()

        url = AppConfig.Connections.url_keycloak_token
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.config.refresh_token,
            'client_id': azp,
        }

        if azp == 'harbor':
            payload.update({'client_id': ConfigClass.harbor_client_secret})

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            self.update_token(response.json()['access_token'], response.json()['refresh_token'])
        elif response.status_code == 401:
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TOKEN, if_exit=True)
        else:
            SrvErrorHandler.default_handle(response.content)

    def refresh_api_key(self) -> None:
        access_token = exchange_api_key(self.config.api_key)
        if access_token is None:
            return SrvErrorHandler.default_handle(
                f'Unable to get access token using "{LoginMethod.API_KEY.value}" method. Unable to proceed.', True
            )

        self.update_token(access_token, '')
