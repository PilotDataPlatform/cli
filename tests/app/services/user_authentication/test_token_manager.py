# Copyright (C) 2023-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import time

import jwt
import pytest
from httpx import HTTPStatusError

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.services.user_authentication.token_manager import SrvTokenManager
from tests.conftest import decoded_token


class TestSrvTokenManager:
    def test_refresh_calls_refresh_token_method_when_is_api_key_method_returns_true(self, httpx_mock, fake, mocker):
        user_config = UserConfig()
        user_config.access_token = jwt.encode({'aud': 'api-key'}, key='')
        user_config.refresh_token = jwt.encode({'refresh': 'token'}, key='')
        manager = SrvTokenManager()
        mocker.patch.object(manager, 'is_api_key', return_value=True)
        httpx_mock.add_response(
            method='POST',
            url=AppConfig.Connections.url_keycloak_token,
            json={'access_token': user_config.access_token, 'refresh_token': user_config.refresh_token},
        )

        manager.refresh(fake.pystr())

    def test_refresh_success_with_refresh_token(self, httpx_mock, fake, mocker):
        manager = SrvTokenManager()
        mocker.patch(
            'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
            return_value=decoded_token(),
        )

        httpx_mock.add_response(
            method='POST',
            url=AppConfig.Connections.url_keycloak_token,
            status_code=401,
        )

        login_using_api_key_mock = mocker.patch(
            'app.services.user_authentication.token_manager.login_using_api_key', return_value=True
        )
        manager.refresh('test_azp')

        assert login_using_api_key_mock.call_count == 1

    def test_refresh_failed_with_invalid_access_refresh_token_apikey(self, httpx_mock, mocker, settings, capsys):
        manager = SrvTokenManager()
        mocker.patch(
            'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
            return_value=decoded_token(),
        )

        httpx_mock.add_response(
            method='POST',
            url=AppConfig.Connections.url_keycloak_token,
            status_code=401,
        )

        login_using_api_key_mock = mocker.patch(
            'app.services.user_authentication.token_manager.login_using_api_key', return_value=False
        )
        out, _ = capsys.readouterr()
        with pytest.raises(SystemExit):
            with pytest.raises(HTTPStatusError):
                manager.refresh('test_azp')
        out, _ = capsys.readouterr()

        assert out.rstrip() == 'Your login session has expired. Please try again or log in again.'
        assert login_using_api_key_mock.call_count == 1

    def test_check_valid_return_0_with_valid_access_token(self):
        user_config = UserConfig()
        user_config.access_token = jwt.encode(
            {'aud': 'api-key', 'exp': time.time() + 100 + AppConfig.Env.token_warn_need_refresh, 'azp': 'test'}, key=''
        )

        manager = SrvTokenManager()
        assert manager.check_valid('test') == 0

    def test_check_valid_return_1_when_need_refresh(self):
        user_config = UserConfig()
        user_config.access_token = jwt.encode(
            {'aud': 'api-key', 'exp': time.time() + AppConfig.Env.token_warn_need_refresh, 'azp': 'test'}, key=''
        )

        manager = SrvTokenManager()
        assert manager.check_valid('test') == 1

    def test_check_valid_return_1_when_access_expire_with_refresh_token(self):
        user_config = UserConfig()
        user_config.access_token = jwt.encode({'aud': 'api-key', 'exp': time.time() - 100, 'azp': 'test'}, key='')
        user_config.refresh_token = jwt.encode({'refresh': 'token', 'exp': time.time() + 100}, key='')

        manager = SrvTokenManager()
        assert manager.check_valid('test') == 1

    def test_check_valid_return_1_when_access_refresh_token_expired_with_api_key(self, mocker):
        user_config = UserConfig()
        user_config.access_token = jwt.encode({'aud': 'api-key', 'exp': time.time() - 100, 'azp': 'test'}, key='')
        user_config.refresh_token = jwt.encode({'refresh': 'token', 'exp': time.time() - 100}, key='')
        user_config.api_key = 'test'
        login_using_api_key_mock = mocker.patch(
            'app.services.user_authentication.token_manager.login_using_api_key', return_value=True
        )

        manager = SrvTokenManager()
        assert manager.check_valid('test') == 1
        assert login_using_api_key_mock.call_count == 1

    def test_check_valid_return_system_error_when_all_expired(self, mocker):
        user_config = UserConfig()
        user_config.access_token = jwt.encode({'aud': 'api-key', 'exp': time.time() - 100, 'azp': 'test'}, key='')
        user_config.refresh_token = jwt.encode({'refresh': 'token', 'exp': time.time() - 100}, key='')
        user_config.api_key = 'test'
        login_using_api_key_mock = mocker.patch(
            'app.services.user_authentication.token_manager.login_using_api_key', return_value=True
        )

        try:
            manager = SrvTokenManager()
            manager.check_valid('test')
        except SystemError:
            pass
        else:
            assert AssertionError('SystemError not raised')

        assert login_using_api_key_mock.call_count == 1
