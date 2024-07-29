# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import time
from typing import Any
from typing import Dict
from typing import Tuple
from typing import Union
from uuid import uuid4

import jwt
from httpx import HTTPStatusError

from app.configs.app_config import AppConfig
from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig
from app.services.clients.base_client import BaseClient
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.message_handler import SrvOutPutHandler


def exchange_api_key(api_key: str) -> Union[Tuple[str, str], Tuple[None, None]]:
    """Exchange API Key with JWT token using Keycloak."""
    http_client = BaseClient(AppConfig.Connections.url_keycloak_realm)
    try:
        response = http_client._get(f'api-key/{api_key}')
        response.raise_for_status()
    except HTTPStatusError:
        return None, None

    response = response.json()
    return response.get('access_token'), response.get('refresh_token')


def login_using_api_key(api_key: str) -> bool:
    """Try to log in using API Key and store results in user config."""

    access_token, refresh_token = exchange_api_key(api_key)
    if access_token is None:
        return False

    decoded_token = jwt.decode(access_token, options={'verify_signature': False}, algorithms=['RS256'])
    username = decoded_token['preferred_username']

    user_config = UserConfig()
    user_config.api_key = api_key
    user_config.access_token = access_token
    user_config.refresh_token = refresh_token
    user_config.username = username
    user_config.last_active = str(int(time.time()))
    user_config.session_id = 'cli-' + str(uuid4())
    user_config.save()

    return True


def user_device_id_login() -> Dict[str, Any]:
    """Get device code URL for user login."""
    http_client = BaseClient(AppConfig.Connections.url_keycloak)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'client_id': ConfigClass.keycloak_device_client_id}
    try:
        resp = http_client._post('auth/device', data=data, headers=headers)
        device_data = resp.json()
        return {
            'expires': device_data['expires_in'],
            'interval': device_data['interval'],
            'device_code': device_data['device_code'],
            'verification_uri_complete': device_data['verification_uri_complete'],
        }
    except HTTPStatusError:
        return {}


def validate_user_device_login(device_code: str, expires: int, interval: int) -> bool:
    """Validate user device authentication."""

    time.sleep(interval)
    http_client = BaseClient(AppConfig.Connections.url_keycloak)
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'device_code': device_code,
        'client_id': ConfigClass.keycloak_device_client_id,
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
    }
    waiting_result, get_result = True, False
    start = time.time()
    SrvOutPutHandler.check_login_device_validation()
    while waiting_result:
        time.sleep(interval)
        try:
            resp = http_client._post('token', data=data, headers=headers)
            if resp.status_code == 200:
                waiting_result = False
                get_result = True
        except HTTPStatusError:
            pass
        end = time.time()
        if end - start >= expires:
            waiting_result = False

    if get_result is False:
        return False

    resp_dict = resp.json()
    decode_token = jwt.decode(resp_dict['access_token'], options={'verify_signature': False}, algorithms=['RS256'])
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
