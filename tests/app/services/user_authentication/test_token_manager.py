# Copyright (C) 2023-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import jwt
import pytest

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.services.user_authentication.token_manager import SrvTokenManager
from tests.conftest import decoded_token


class TestSrvTokenManager:
    def test_is_api_key_returns_true_when_audience_has_api_key_entry(self):
        user_config = UserConfig()
        user_config.access_token = jwt.encode({'aud': 'api-key'}, key='').decode()
        manager = SrvTokenManager()

        assert manager.is_api_key() is True

    def test_refresh_calls_refresh_token_method_when_is_api_key_method_returns_true(self, requests_mock, fake):
        user_config = UserConfig()
        user_config.access_token = jwt.encode({'aud': 'api-key'}, key='').decode()
        user_config.refresh_token = jwt.encode({'refresh': 'token'}, key='').decode()
        manager = SrvTokenManager()
        requests_mock.post(
            AppConfig.Connections.url_keycloak_token,
            json={'access_token': user_config.access_token, 'refresh_token': user_config.refresh_token},
        )

        manager.refresh(fake.pystr())

    def test_refresh_failed_with_invalid_token(self, requests_mock, mocker, settings, capsys):
        manager = SrvTokenManager()
        mocker.patch(
            'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
            return_value=decoded_token(),
        )

        requests_mock.post(
            AppConfig.Connections.url_keycloak_token,
            status_code=401,
        )

        with pytest.raises(SystemExit):
            manager.refresh('test_azp')
        out, _ = capsys.readouterr()
        assert out.rstrip() == 'Your login session has expired. Please try again or log in again.'
