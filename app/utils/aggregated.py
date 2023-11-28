# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import os
import re
import shutil
from typing import Any
from typing import List

import httpx
import requests

from app.configs.app_config import AppConfig
from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token


def resilient_session():
    # each resilient session will
    headers = {'VM-Info': ConfigClass.vm_info}
    client = httpx.Client(headers=headers, timeout=None)
    return client


@require_valid_token()
def search_item(project_code, zone, folder_relative_path, item_type, container_type='project'):
    token = UserConfig().access_token
    url = AppConfig.Connections.url_bff + '/v1/project/{}/search'.format(project_code)
    params = {
        'zone': zone,
        'project_code': project_code,
        'path': folder_relative_path,
        'item_type': item_type,
        'container_type': container_type,
    }
    headers = {'Authorization': 'Bearer ' + token}
    res = requests.get(url, params=params, headers=headers)
    if res.status_code == 403:
        SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, project_code)
    elif res.status_code == 404:
        pass
    elif res.status_code != 200:
        SrvErrorHandler.default_handle(res.text, True)

    return res.json()


@require_valid_token()
def get_file_info_by_geid(geid: list):
    token = UserConfig().access_token
    payload = {'geid': geid}
    headers = {'Authorization': 'Bearer ' + token}
    url = AppConfig.Connections.url_bff + '/v1/query/geid'
    res = resilient_session().post(url, headers=headers, json=payload)
    return res.json()['result']


def fit_terminal_width(string_to_format):
    string_to_format = string_to_format.rsplit('...')
    current_len = 0
    sentence = ''
    terminal_width = shutil.get_terminal_size().columns
    for word in string_to_format:
        word_len = len(word)
        if current_len + word_len < terminal_width and word != '\n':
            current_len = current_len + word_len + 1
            sentence = sentence + word + ' '
        elif word == '\n':
            current_len = 1
            sentence = sentence + '\n'
        else:
            current_len = len(word) + 1
            sentence = sentence + '\n' + word + ' '
    return sentence


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


def doc(arg):
    """Docstring decorator."""

    def decorator(func):
        func.__doc__ = arg
        return func

    return decorator


def get_file_in_folder(path):
    path = path if isinstance(path, list) else [path]
    files_list = []
    for _path in path:
        if os.path.isdir(_path):
            for path, _, files in os.walk(_path):
                for name in files:
                    file = os.path.join(path, name)
                    files_list.append(file)
        else:
            files_list.append(_path)
    return files_list


def identify_target_folder(project_path):
    project_code = project_path.split('/')[0]
    if len(project_path.split('/')) > 1:
        target_folder = '/'.join(project_path.split('/')[1:])
        for f in target_folder.split('/'):
            f = f.strip(' ')
            valid = validate_folder_name(f)
            if not valid:
                SrvErrorHandler.customized_handle(ECustomizedError.INVALID_FOLDERNAME, True)
    else:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_NAMEFOLDER, True)
        target_folder = ''
    return project_code, target_folder


def batch_generator(iterable: List[Any], batch_size=1):
    max_size = len(iterable)
    for start_index in range(0, max_size, batch_size):
        yield iterable[start_index : min(start_index + batch_size, max_size)]
