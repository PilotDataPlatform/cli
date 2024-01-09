# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pytest

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.services.user_authentication.user_login_logout import check_is_login
from app.services.user_authentication.user_login_logout import user_device_id_login
from app.services.user_authentication.user_login_logout import validate_user_device_login


def test_check_is_not_login(mocker):
    mocker.patch('app.configs.user_config.UserConfig.is_logged_in', return_value=False)
    expected_result = False
    with pytest.raises(SystemExit):
        actual = check_is_login()
        assert actual == expected_result


def test_user_device_id_login_success(monkeypatch, requests_mock):
    monkeypatch.setattr(AppConfig.Connections, 'url_keycloak', 'http://url_keycloak')
    requests_mock.post(
        'http://url_keycloak/auth/device',
        json={
            'expires_in': 10,
            'interval': 1,
            'device_code': 'ANY',
            'verification_uri_complete': 'http://any/?user_code=Any',
        },
    )
    result = user_device_id_login()
    assert result == {
        'expires': 10,
        'interval': 1,
        'device_code': 'ANY',
        'verification_uri_complete': 'http://any/?user_code=Any',
    }


def test_user_device_id_login_error(monkeypatch, requests_mock):
    monkeypatch.setattr(AppConfig.Connections, 'url_keycloak', 'http://url_keycloak')
    requests_mock.post('http://url_keycloak/auth/device', status_code=400, json={})
    result = user_device_id_login()
    assert result == {}


def test_validate_user_device_login_success(monkeypatch, requests_mock):
    monkeypatch.setattr(AppConfig.Connections, 'url_keycloak_token', 'http://url_keycloak/token')
    token = (
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwicHJlZmVycmVkX3VzZXJuYW'
        '1lIjoiSm9obiBEb2UiLCJpYXQiOjE1MTYyMzkwMjJ9.0sw4vF5BGhhnv2BMfrxQuNMgFU3mxZpVPsOfkvPWgjs'
    )
    requests_mock.post('http://url_keycloak/token', json={'access_token': token, 'refresh_token': 'refresh'})
    result = validate_user_device_login('any', 1, 0.1)
    assert result
    user = UserConfig()
    assert user.username == 'John Doe'
    assert user.access_token == token
    assert user.refresh_token == 'refresh'


def test_validate_user_device_login_error(monkeypatch, requests_mock):
    monkeypatch.setattr(AppConfig.Connections, 'url_keycloak_token', 'http://url_keycloak/token')
    requests_mock.post('http://url_keycloak/token', status_code=400, json={})
    result = validate_user_device_login('any', 0.2, 0.1)
    assert not result
