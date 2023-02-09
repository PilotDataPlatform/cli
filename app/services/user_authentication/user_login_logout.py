# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time
from typing import Any
from typing import Dict
from uuid import uuid4

import jwt
import requests

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.message_handler import SrvOutPutHandler


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
        user_config.session_id = 'cli-' + str(uuid4())
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


def user_device_id_login() -> Dict[str, Any]:
    """Get device code URL for user login."""

    url = f'{AppConfig.Connections.url_keycloak}/auth/device'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'client_id': AppConfig.Env.keycloak_device_client_id}
    resp = requests.post(url, headers=headers, data=data)
    if resp.status_code == 200:
        device_data = resp.json()
        return {
            'expires': device_data['expires_in'],
            'interval': device_data['interval'],
            'device_code': device_data['device_code'],
            'verification_uri_complete': device_data['verification_uri_complete'],
        }
    return {}


def validate_user_device_login(device_code: str, exipres: int, interval: int) -> bool:
    """Validate user device authentication."""

    time.sleep(interval)
    url = AppConfig.Connections.url_keycloak_token
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'device_code': device_code,
        'client_id': AppConfig.Env.keycloak_device_client_id,
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
    }
    waiting_result = True
    start = time.time()
    SrvOutPutHandler.check_login_device_validation()
    while waiting_result:
        time.sleep(0.1)
        resp = requests.post(url, headers=headers, data=data)
        end = time.time()
        if resp.status_code == 200:
            waiting_result = False
        if end - start >= exipres:
            waiting_result = False

    if resp.status_code != 200:
        return False

    resp_dict = resp.json()
    decode_token = jwt.decode(resp_dict['access_token'], verify=False)
    user_config = UserConfig()
    user_config.access_token = resp_dict['access_token']
    user_config.refresh_token = resp_dict['refresh_token']
    user_config.username = decode_token['preferred_username']
    user_config.last_active = str(int(time.time()))
    user_config.hpc_token = ''
    user_config.session_id = 'cli-' + str(uuid4())
    user_config.save()

    return resp_dict


def check_is_login(if_print: bool = True) -> bool:
    user_config = UserConfig()
    has_username = user_config.config.has_option('USER', 'username')
    has_access_token = user_config.config.has_option('USER', 'access_token')
    has_refresh_token = user_config.config.has_option('USER', 'refresh_token')
    if has_username and has_access_token and has_refresh_token and user_config.username != '':
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
