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
    def test_refresh_calls_refresh_token_method_when_is_api_key_method_returns_true(self, requests_mock, fake, mocker):
        user_config = UserConfig()
        user_config.access_token = jwt.encode({'aud': 'api-key'}, key='')
        user_config.refresh_token = jwt.encode({'refresh': 'token'}, key='')
        manager = SrvTokenManager()
        mocker.patch.object(manager, 'is_api_key', return_value=True)
        refresh_api_key_mock = mocker.patch.object(manager, 'refresh_api_key')
        requests_mock.post(
            AppConfig.Connections.url_keycloak_token,
            json={'access_token': user_config.access_token, 'refresh_token': user_config.refresh_token},
        )

        manager.refresh(fake.pystr())
        assert refresh_api_key_mock.call_count == 1

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

        login_using_api_key_mock = mocker.patch(
            'app.services.user_authentication.token_manager.login_using_api_key', return_value=False
        )
        out, _ = capsys.readouterr()
        with pytest.raises(SystemExit):
            manager.refresh('test_azp')
        out, _ = capsys.readouterr()
        assert out.rstrip() == 'Your login session has expired. Please try again or log in again.'
        assert login_using_api_key_mock.call_count == 1
