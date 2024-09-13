# Copyright (C) 2023-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import jwt
import pytest
from packaging.version import Version

import app.services.output_manager.message_handler as mhandler
from app.commands.user import login
from app.configs.app_config import AppConfig
from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig


def test_login_command_with_api_key_option_calls_keycloak_and_stores_response_in_user_config(
    httpx_mock, cli_runner, fake, mocker
):
    username = fake.user_name()
    api_key = fake.pystr(20)
    access_token = jwt.encode({'preferred_username': username}, key='')
    refresh_token = jwt.encode({'type': 'refresh', 'token': fake.pystr(20)}, key='')
    httpx_mock.add_response(
        method='GET',
        url=f'{AppConfig.Connections.url_keycloak_realm}/{ConfigClass.apikey_endpoint}/{api_key}',
        status_code=200,
        json={'access_token': access_token, 'refresh_token': refresh_token},
    )
    mocker.patch('app.commands.user.get_latest_cli_version', return_value=Version('1.0.0'))

    result = cli_runner.invoke(login, ['--api-key', api_key])

    assert result.exit_code == 0
    assert 'Trying to log in using "api-key" method.' in result.output

    user = UserConfig()
    assert user.access_token == access_token
    assert user.refresh_token == refresh_token
    assert user.username == username


def test_login_command_without_api_key_option_takes_value_from_environment_variable(
    monkeypatch, mocker, cli_runner, fake
):
    api_key = fake.pystr(20)
    monkeypatch.setenv('PILOT_API_KEY', api_key)
    login_using_api_key_mock = mocker.patch('app.commands.user.login_using_api_key', return_value=True)
    mocker.patch('app.commands.user.get_latest_cli_version', return_value=Version('1.0.0'))

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
    mocker.patch('app.commands.user.get_latest_cli_version', return_value=Version('1.0.0'))

    result = cli_runner.invoke(login)

    assert result.exit_code == 0
    assert 'Trying to log in using "device-code" method.' in result.output

    user_device_id_login_mock.assert_called_once()
    validate_user_device_login_mock.assert_called_once_with(
        device_login['device_code'], device_login['expires'], device_login['interval']
    )


@pytest.mark.parametrize(
    'current_version, new_version',
    [
        ('1.0.0', '0.1.0'),
        ('1.0.0', '10.0.0'),
        ('1.0.0', '1.0.0a0'),
        ('1.0.0', '1.1.0'),
        ('2.0.0', '2.0.0'),
        ('10.0.0', '1.0.0'),
    ],
)
def test_login_command_with_newer_version_available_message(
    mocker, cli_runner, fake, monkeypatch, current_version, new_version, httpx_mock
):
    api_key = fake.pystr(20)
    monkeypatch.setenv('PILOT_API_KEY', api_key)
    login_using_api_key_mock = mocker.patch('app.commands.user.login_using_api_key', return_value=True)
    access_token_exists = mocker.patch('app.utils.aggregated.UserConfig.is_access_token_exists', return_value=True)

    httpx_mock.add_response(
        url=AppConfig.Connections.url_download_greenroom + '/v2/download/cli',
        status_code=200,
        json={'result': {'linux': {'version': new_version}}},
    )
    mocker.patch('pkg_resources.get_distribution', return_value=mocker.Mock(version=current_version))

    result = cli_runner.invoke(login)

    assert result.exit_code == 0
    assert login_using_api_key_mock.called_once_with(api_key)
    assert access_token_exists.called_once()
    if Version(current_version) < Version(new_version):
        assert mhandler.SrvOutPutHandler.newer_version_available(new_version) in result.output


# nothing should be printed out
def test_login_command_when_url_link_fails(mocker, cli_runner, fake, monkeypatch, httpx_mock):
    api_key = fake.pystr(20)
    monkeypatch.setenv('PILOT_API_KEY', api_key)
    mocker.patch('app.commands.user.login_using_api_key', return_value=True)
    access_token_exists = mocker.patch('app.utils.aggregated.UserConfig.is_access_token_exists', return_value=True)

    httpx_mock.add_response(
        url=AppConfig.Connections.url_download_greenroom + '/v2/download/cli',
        status_code=404,
        json={'error': 'Not Found'},
    )
    mocker.patch('pkg_resources.get_distribution', return_value=mocker.Mock(version='1.0.0'))

    result = cli_runner.invoke(login)
    assert result.exit_code == 0
    assert access_token_exists.called_once()


# nothing should be printed out
def test_help_command_without_login(mocker, cli_runner, fake, monkeypatch, httpx_mock):
    api_key = fake.pystr(20)
    monkeypatch.setenv('PILOT_API_KEY', api_key)
    mocker.patch('app.commands.user.login_using_api_key', return_value=True)
    access_token_exists = mocker.patch('app.utils.aggregated.UserConfig.is_access_token_exists', return_value=True)
    mocker.patch('pkg_resources.get_distribution', return_value=mocker.Mock(version='1.0.0'))

    result = cli_runner.invoke(login)
    assert result.exit_code == 0
    assert access_token_exists.called_once()
