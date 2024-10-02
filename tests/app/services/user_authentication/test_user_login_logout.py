# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import pytest

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.resources.custom_error import Error
from app.services.output_manager.error_handler import ECustomizedError
from app.services.user_authentication.user_login_logout import check_is_login
from app.services.user_authentication.user_login_logout import user_device_id_login
from app.services.user_authentication.user_login_logout import user_login
from app.services.user_authentication.user_login_logout import validate_user_device_login


def test_user_login_success(requests_mock):
    requests_mock.post(
        'http://service_auth',
        json={
            'code': 200,
            'error_msg': '',
            'page': 0,
            'total': 1,
            'num_of_pages': 1,
            'result': {
                'access_token': 'fake-token',
                'expires_in': 300,
                'refresh_expires_in': 360,
                'refresh_token': 'refresh-token',
                'token_type': 'Bearer',
                'not-before-policy': 0,
                'session_state': 'session-state',
                'scope': 'roles groups profile email',
            },
        },
    )
    res = user_login('username', 'password')
    assert res.get('code') == 200
    assert res['result'].get('access_token') == 'fake-token'
    assert res['result'].get('refresh_token') == 'refresh-token'
    assert res.get('error_msg') == ''


def test_user_login_wrong_password(requests_mock, capsys):
    requests_mock.post(
        'http://service_auth',
        json={
            'code': 401,
            'error_msg': "401: b'{\"error\":\"invalid_grant\",\"error_description\":\"Invalid user credentials\"}'",
            'page': 0,
            'total': 1,
            'num_of_pages': 1,
            'result': [],
        },
        status_code=401,
    )
    with pytest.raises(SystemExit):
        user_login('username', 'password')
    out, err = capsys.readouterr()
    assert out == Error.error_msg.get(ECustomizedError.INVALID_CREDENTIALS.name, 'Unknown error.') + '\n'
    assert err == ''


def test_check_is_not_login(mocker):
    mocker.patch('configparser.ConfigParser.has_option', return_value=False)
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
