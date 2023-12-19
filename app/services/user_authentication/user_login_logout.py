# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import time
from typing import Any
from typing import Dict
from typing import Union
from uuid import uuid4

import jwt
import requests
from requests import RequestException

from app.configs.app_config import AppConfig
from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.message_handler import SrvOutPutHandler


def exchange_api_key(api_key: str) -> Union[str, None]:
    """Exchange API Key with JWT token using Keycloak."""

    url = f'{ConfigClass.keycloak_realm_url}/api-key/{api_key}'
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except RequestException:
        return None

    return response.json()['access_token']


def login_using_api_key(api_key: str) -> bool:
    """Try to log in using API Key and store results in user config."""

    access_token = exchange_api_key(api_key)
    if access_token is None:
        return False

    decoded_token = jwt.decode(access_token, verify=False)
    username = decoded_token['preferred_username']

    user_config = UserConfig()
    user_config.api_key = api_key
    user_config.access_token = access_token
    user_config.refresh_token = ''
    user_config.username = username
    user_config.last_active = str(int(time.time()))
    user_config.session_id = 'cli-' + str(uuid4())
    user_config.save()

    return True


def user_device_id_login() -> Dict[str, Any]:
    """Get device code URL for user login."""

    url = f'{AppConfig.Connections.url_keycloak}/auth/device'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'client_id': ConfigClass.keycloak_device_client_id}
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


def validate_user_device_login(device_code: str, expires: int, interval: int) -> bool:
    """Validate user device authentication."""

    time.sleep(interval)
    url = AppConfig.Connections.url_keycloak_token
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'device_code': device_code,
        'client_id': ConfigClass.keycloak_device_client_id,
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
    }
    waiting_result = True
    start = time.time()
    SrvOutPutHandler.check_login_device_validation()
    while waiting_result:
        time.sleep(0.1)
        resp = requests.post(url, headers=headers, data=data)
        end = time.time()
        if end - start >= expires:
            waiting_result = False
        elif resp.status_code == 200:
            waiting_result = False

    if resp.status_code != 200:
        return False

    resp_dict = resp.json()
    decode_token = jwt.decode(resp_dict['access_token'], verify=False)
    user_config = UserConfig()
    user_config.api_key = ''
    user_config.access_token = resp_dict['access_token']
    user_config.refresh_token = resp_dict['refresh_token']
    user_config.username = decode_token['preferred_username']
    user_config.last_active = str(int(time.time()))
    user_config.session_id = 'cli-' + str(uuid4())
    user_config.save()

    return True


def check_is_login(if_print: bool = True) -> bool:
    user_config = UserConfig()
    if user_config.is_logged_in():
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
        'client_secret': ConfigClass.harbor_client_secret,
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
