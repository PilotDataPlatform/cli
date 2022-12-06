# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time

import requests

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler


def user_login(username, password):
    url = AppConfig.Connections.url_authn
    user_config = UserConfig()
    request_body = {'username': username, 'password': password}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=request_body, headers=headers)
    if response.status_code == 200:
        res_to_dict = response.json()
        user_config.username = username
        user_config.password = password
        user_config.access_token = res_to_dict['result']['access_token']
        user_config.refresh_token = res_to_dict['result']['refresh_token']
        user_config.last_active = str(int(time.time()))
        user_config.hpc_token = ''
        user_config.session_id = 'cli-' + str(int(time.time()))
        user_config.save()
    elif response.status_code == 401:
        res_to_dict = []
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_CREDENTIALS, True)
    else:
        if response.text:
            SrvErrorHandler.default_handle(response.text, True)
        res_to_dict = response.json()
        SrvErrorHandler.default_handle(response.content, True)
    return res_to_dict


def check_is_login(if_print=True):
    user_config = UserConfig()
    has_username = user_config.config.has_option('USER', 'username')
    has_password = user_config.config.has_option('USER', 'password')
    if has_username and has_password and user_config.username != '':
        return True
    else:
        SrvErrorHandler.customized_handle(ECustomizedError.LOGIN_SESSION_INVALID, if_print) if if_print else None
        return False


def check_is_active(if_print=True):
    user_config = UserConfig()
    last_active = user_config.config['USER']['last_active']
    now = int(time.time())
    if now - int(last_active) < AppConfig.Env.session_duration:
        user_config.last_active = str(now)
        user_config.save()
        return True
    else:
        user_config.clear()
        SrvErrorHandler.customized_handle(ECustomizedError.LOGIN_SESSION_INVALID, if_print) if if_print else None
        return False


def user_logout():
    user_config = UserConfig()
    user_config.clear()


def request_default_tokens(username, password):
    url = AppConfig.Connections.url_authn
    payload = {'username': username, 'password': password}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return [response.json()['result']['access_token'], response.json()['result']['refresh_token']]
    elif response.status_code == 401:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_CREDENTIALS, True)
    else:
        if response.text:
            SrvErrorHandler.default_handle(response.text, True)
        SrvErrorHandler.default_handle(response.content, True)


def request_harbor_tokens(username, password):
    url = AppConfig.Connections.url_keycloak
    payload = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_id': 'harbor',
        'client_secret': AppConfig.Env.harbor_client_secret,
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, data=payload, headers=headers, verify=False)
    if response.status_code == 200:
        return [response.json()['access_token'], response.json()['refresh_token']]
    elif response.status_code == 401:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_CREDENTIALS, True)
    else:
        if response.text:
            SrvErrorHandler.default_handle(response.text, True)
        SrvErrorHandler.default_handle(response.content, True)


def get_tokens(username, password, azp=None):
    if not azp or azp == 'kong':
        return request_default_tokens(username, password)
    elif azp == 'harbor':
        return request_harbor_tokens(username, password)
