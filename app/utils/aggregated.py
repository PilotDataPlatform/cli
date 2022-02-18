import datetime
import requests
import shutil
import re
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.configs.app_config import AppConfig
import app.services.output_manager.error_handler as ehandler
import app.services.user_authentication as srv_auth
import app.services.logger_services.log_functions as logger
from app.services.user_authentication.decorator import require_valid_token
from app.services.crypto.crypto import decryption
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler


def get_current_datetime():
    return datetime.datetime.now().isoformat()


def resilient_session():
    s = requests.Session()
    retries = Retry(
        total=AppConfig.Env.resilient_retry,
        backoff_factor=AppConfig.Env.resilient_backoff,
        status_forcelist=AppConfig.Env.resilient_retry_code)
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    return s

def get_user_info():
    '''
    {
        "email_verified":true,
        "name":"admin admin",
        "preferred_username":"admin",
        "given_name":"admin",
        "family_name":"admin",
        "email":"siteadmin.test@example.com"
    }
    '''
    token_mgr = srv_auth.token_manager.SrvTokenManager()
    decoded_token = token_mgr.decode_access_token()
    return decoded_token


@require_valid_token()
def get_source_file(file_relative_path: str, project_code: str, token: str,
                    namespace=AppConfig.Env.core_zone, interactive=True):
    url = AppConfig.Connections.url_bff + "/v1/project/{}/file/exist".format(project_code)
    query = {
        "project_code": project_code,
        "zone": get_zone(namespace),
        "file_relative_path": file_relative_path,
    }
    headers = {
        'Authorization': "Bearer " + token,
    }
    __res = requests.get(url, params=query, headers=headers)
    if __res.status_code == 200:
        return __res.json()['result']
    elif __res.status_code == 404:
        file_relative_path = ' ' if not file_relative_path else file_relative_path
        if not interactive:
            return []
        else:
            ehandler.SrvErrorHandler.customized_handle(
                ehandler.ECustomizedError.INVALID_SOURCE_FILE, interactive,
                value=file_relative_path)
    elif 'invalid' in __res.text or 'Token expired' in __res.text:
        ehandler.SrvErrorHandler.customized_handle(
            ehandler.ECustomizedError.INVALID_TOKEN, interactive)
    else:
        ehandler.SrvErrorHandler.customized_handle(
            ehandler.ECustomizedError.ERROR_CONNECTION, interactive)


def format_to_fit_terminal(string_to_format):
    string_to_format = string_to_format.split('...')
    current_len = 0
    sentence = ""
    terminal_width = shutil.get_terminal_size().columns
    for word in string_to_format:
        word_len = len(word)
        if current_len + word_len < terminal_width and word != "\n":
            current_len = current_len + word_len + 1
            sentence = sentence + word + " "
        elif word == '\n':
            current_len = 1
            sentence = sentence + "\n"
        else:
            current_len = len(word) + 1
            sentence = sentence + "\n" + word + " "
    return sentence


@require_valid_token()
def get_folder_in_project(project_code, zone, folder_relative_path, token):
    url = AppConfig.Connections.url_bff + "/v1/project/{}/folder".format(project_code)
    params = {'zone': zone,
              'project_code': project_code,
              'folder': folder_relative_path}
    headers = {
        'Authorization': "Bearer " + token,
    }
    __res = requests.get(url, params=params, headers=headers)
    if __res.status_code == 200 or __res.status_code == 404:
        return __res.json()['result']
    elif __res.status_code == 403:
        ehandler.SrvErrorHandler.customized_handle(
            ehandler.ECustomizedError.PERMISSION_DENIED, True)
    else:
        ehandler.SrvErrorHandler.customized_handle(
            ehandler.ECustomizedError.ERROR_CONNECTION, True)


def get_zone(zone):
    if zone.lower() == AppConfig.Env.green_zone:
        return AppConfig.Env.green_zone
    elif zone.lower() == AppConfig.Env.core_zone:
        return AppConfig.Env.core_zone
    else:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_ZONE, True)


def validate_folder_name(folder_name):
    regex = re.compile('[/:?.\\*<>|”\']')
    contain_invalid_char = regex.search(folder_name)
    if contain_invalid_char or len(folder_name) > 20 or not folder_name:
        valid = False
    else:
        valid = True
    return valid

@require_valid_token()
def validate_file_status(project_geid, target_path, operator, token, session_id):
    payload = {"operation": "upload",
               "project_geid": project_geid,
               "operator": operator,
               "payload": {
                   "targets": target_path}
               }
    headers = {
        'Authorization': "Bearer " + token,
        'Session-ID': session_id
    }
    url = AppConfig.Connections.url_validation
    res = requests.post(url, headers=headers, json=payload)
    res_json = res.json()
    if res_json.get('code') == 200 and res_json.get('result'):
        file_validation = []
        for v in res_json.get('result'):
            file_validation.append(v.get('is_valid'))
        if len(set(file_validation)) > 1:
            valid = False
        else:
            valid = file_validation[0]
    elif res_json.get('code') != 200:
        valid = False
    else:
        ehandler.SrvErrorHandler.customized_handle(ehandler.ECustomizedError.FOLDER_EMPTY, True)
    return valid

def doc(arg):
    """Docstring decorator."""
    def decorator(func):
        func.__doc__ = arg
        return func
    return decorator

@require_valid_token()
def void_validate_zone(action, zone, token):
    config_path = '/etc/environment'
    current_env_var = ''
    if os.path.isfile(config_path):
        f = open(config_path)
        variables = f.readlines()
        for var in variables:
            if var.startswith('ZONE'):
                current_env_var = var[5:].replace("\n", "").replace('"', "")
    url = AppConfig.Connections.url_bff + "/v1/validate/env"
    headers = {
        'Authorization': "Bearer " + token
    }
    payload = {"action": action, "environ": current_env_var, 'zone': zone}
    res = requests.post(url, headers=headers, json=payload)
    validation_result = res.json().get('result')
    validation_error = res.json().get('error_msg').replace("Invalid action: ", "")
    if validation_result == 'valid':
        pass
    else:
        ehandler.SrvErrorHandler.customized_handle(ehandler.ECustomizedError.INVALID_ACTION, True, f"{validation_error}")

def get_file_in_folder(path):
    path = path if isinstance(path, list) else [path]
    files_list = []
    for _path in path:
        if os.path.isdir(_path):
            for path, subdirs, files in os.walk(_path):
                for name in files:
                    file = os.path.join(path, name)
                    files_list.append(file)
        else:
            files_list.append(_path)
    return files_list
