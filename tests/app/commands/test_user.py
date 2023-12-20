# Copyright (C) 2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import jwt

from app.commands.user import login
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig


def test_login_command_with_api_key_option_calls_keycloak_and_stores_response_in_user_config(
    requests_mock, cli_runner, fake, settings
):
    username = fake.user_name()
    api_key = fake.pystr(20)
    access_token = jwt.encode({'preferred_username': username}, key='').decode()
    requests_mock.get(
        f'{AppConfig.Connections.url_keycloak_realm}/api-key/{api_key}', json={'access_token': access_token}
    )

    result = cli_runner.invoke(login, ['--api-key', api_key])

    assert result.exit_code == 0
    assert 'Trying to log in using "api-key" method.' in result.output

    user = UserConfig()
    assert user.access_token == access_token
    assert user.username == username


def test_login_command_without_api_key_option_takes_value_from_environment_variable(
    monkeypatch, mocker, cli_runner, fake
):
    api_key = fake.pystr(20)
    monkeypatch.setenv('PILOT_API_KEY', api_key)
    login_using_api_key_mock = mocker.patch('app.commands.user.login_using_api_key', return_value=True)

    result = cli_runner.invoke(login)

    assert result.exit_code == 0

    login_using_api_key_mock.assert_called_once_with(api_key)


def test_login_command_without_api_key_option_falls_back_to_device_code_method(mocker, cli_runner, fake):
    device_login = {
        'expires': fake.pyint(),
        'interval': fake.pyint(),
        'device_code': fake.pystr(),
        'verification_uri_complete': fake.url(),
    }
    user_device_id_login_mock = mocker.patch('app.commands.user.user_device_id_login', return_value=device_login)
    validate_user_device_login_mock = mocker.patch('app.commands.user.validate_user_device_login', return_value=True)

    result = cli_runner.invoke(login)

    assert result.exit_code == 0
    assert 'Trying to log in using "device-code" method.' in result.output

    user_device_id_login_mock.assert_called_once()
    validate_user_device_login_mock.assert_called_once_with(
        device_login['device_code'], device_login['expires'], device_login['interval']
    )
