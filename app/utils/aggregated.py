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

import datetime
import os
import re
import shutil

import httpx
import requests

from app.configs.app_config import AppConfig
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token
from env import ConfigClass


def get_current_datetime():
    return datetime.datetime.now().isoformat()


def resilient_session():
    # each resilient session will
    headers = {'vm-info': ConfigClass.VM_INFO}
    client = httpx.Client(headers=headers)
    return client


@require_valid_token()
def search_item(project_code, zone, folder_relative_path, item_type, token, container_type='project'):
    url = AppConfig.Connections.url_bff + '/v1/project/{}/search'.format(project_code)
    params = {
        'zone': zone,
        'project_code': project_code,
        'path': folder_relative_path,
        'item_type': item_type,
        'container_type': container_type,
    }
    headers = {
        'Authorization': 'Bearer ' + token,
    }
    __res = requests.get(url, params=params, headers=headers)
    return __res.json()


@require_valid_token()
def get_file_info_by_geid(geid: list, token):
    payload = {'geid': geid}
    headers = {'Authorization': 'Bearer ' + token}
    url = AppConfig.Connections.url_bff + '/v1/query/geid'
    res = resilient_session().post(url, headers=headers, json=payload)
    return res.json()['result']


def fit_terminal_width(string_to_format):
    string_to_format = string_to_format.split('...')
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


# @require_valid_token()
# def void_validate_zone(action, zone, project_code):
#     user = UserConfig()
#     url = AppConfig.Connections.url_bff + '/v1/validate/env'
#     headers = {'Authorization': 'Bearer ' + user.access_token, 'VM_Info': ConfigClass.VM_INFO_1}
#     payload = {'action': action, 'environ': 'current_env_var', 'zone': zone, 'project_code': project_code}
#     res = requests.post(url, headers=headers, json=payload)
#     validation_result = res.json().get('result')
#     validation_error = res.json().get('error_msg').replace('Invalid action: ', '')
#     if validation_result == 'valid':
#         pass
#     else:
#         SrvErrorHandler.customized_handle(ECustomizedError.INVALID_ACTION, True, f'{validation_error}')


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
