import requests
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
import app.services.logger_services.log_functions as logger
import app.services.output_manager.error_handler as ehandler
import time


def user_login(username, password):
    url = AppConfig.Connections.url_authn
    user_config = UserConfig()
    request_body = {
        "username": username,
        "password": password
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=request_body, headers=headers)
    if response.status_code == 200:
        res_to_dict = response.json()
        user_config.username = username
        user_config.password = password
        user_config.access_token = res_to_dict['result']['access_token']
        user_config.refresh_token = res_to_dict['result']['refresh_token']
        user_config.last_active = str(int(time.time()))
        user_config.hpc_token = ""
        user_config.save()
    elif response.status_code == 401:
        res_to_dict = []
        ehandler.SrvErrorHandler.customized_handle(
            ehandler.ECustomizedError.INVALID_CREDENTIALS,
            True)
    else:
        if response.text:
            ehandler.SrvErrorHandler.default_handle(
                response.text,
                True
            )
        res_to_dict = response.json()
        ehandler.SrvErrorHandler.default_handle(
            response.content,
            True)
    return res_to_dict

def check_is_login(if_print=True):
    user_config = UserConfig()
    if user_config.config.has_option("USER", "username") and \
        user_config.config.has_option("USER", "password") and user_config.config['USER']["username"] != "":
        return True
    else:
        ehandler.SrvErrorHandler.customized_handle(
            ehandler.ECustomizedError.LOGIN_SESSION_INVALID, if_print) if if_print else None
        return False

def check_is_active(if_print=True):
    user_config = UserConfig()
    last_active = user_config.config['USER']["last_active"]
    now = int(time.time())
    if now - int(last_active) < AppConfig.Env.session_duration:
        user_config.last_active = str(now)
        user_config.save()
        return True
    else:
        user_config.clear()
        ehandler.SrvErrorHandler.customized_handle(
            ehandler.ECustomizedError.LOGIN_SESSION_INVALID, if_print) if if_print else None
        return False

def user_logout():
    user_config = UserConfig()
    user_config.clear()

def request_default_tokens(username, password):
    url = AppConfig.Connections.url_authn
    payload = {
        'username': username,
        'password': password
    }
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return [response.json()['result']['access_token'], response.json()['result']['refresh_token']]
    elif response.status_code == 401:
        ehandler.SrvErrorHandler.customized_handle(ehandler.ECustomizedError.INVALID_CREDENTIALS, True)
    else:
        if response.text:
            ehandler.SrvErrorHandler.default_handle(response.text, True)
        ehandler.SrvErrorHandler.default_handle(response.content, True)

def request_harbor_tokens(username, password):
    url = AppConfig.Connections.url_keycloak
    payload = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_id': 'harbor',
        'client_secret': AppConfig.Env.harbor_client_secret
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(url, data=payload, headers=headers, verify=False)
    if response.status_code == 200:
        return [response.json()['access_token'], response.json()['refresh_token']]
    elif response.status_code == 401:
        ehandler.SrvErrorHandler.customized_handle(ehandler.ECustomizedError.INVALID_CREDENTIALS, True)
    else:
        if response.text:
            ehandler.SrvErrorHandler.default_handle(response.text, True)
        ehandler.SrvErrorHandler.default_handle(response.content, True)

def get_tokens(username, password, azp=None):
    if not azp or azp == 'kong':
        return request_default_tokens(username, password)
    elif azp == 'harbor':
        return request_harbor_tokens(username, password)
