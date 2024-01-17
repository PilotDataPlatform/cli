# Copyright (C) 2023-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import jwt

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.services.user_authentication.token_manager import SrvTokenManager


class TestSrvTokenManager:
    def test_is_api_key_returns_true_when_audience_has_api_key_entry(self):
        user_config = UserConfig()
        user_config.access_token = jwt.encode({'aud': 'api-key'}, key='').decode()
        manager = SrvTokenManager()

        assert manager.is_api_key() is True

    def test_refresh_calls_refresh_api_key_method_when_is_api_key_method_returns_true(self, mocker, fake):
        user_config = UserConfig()
        user_config.access_token = jwt.encode({'aud': 'api-key'}, key='').decode()
        manager = SrvTokenManager()
        refresh_api_key_mock = mocker.patch.object(manager, 'refresh_api_key')

        manager.refresh(fake.pystr())

        refresh_api_key_mock.assert_called_once()

    def test_refresh_api_key_calls_keycloak_and_stores_access_token_in_config(self, requests_mock, settings):
        manager = SrvTokenManager()
        access_token = jwt.encode({}, key='').decode()
        requests_mock.get(
            f'{AppConfig.Connections.url_keycloak_realm}/api-key/{manager.config.api_key}',
            json={'access_token': access_token},
        )

        manager.refresh_api_key()

        assert manager.config.access_token == access_token
        assert manager.config.refresh_token == ''
