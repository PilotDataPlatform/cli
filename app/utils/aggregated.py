# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import os
import re
import shutil
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import httpx
import requests

import app.services.logger_services.log_functions as logger
from app.configs.app_config import AppConfig
from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig
from app.models.item import ItemType
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token


def resilient_session():
    # each resilient session will
    headers = {'VM-Info': ConfigClass.vm_info}
    client = httpx.Client(headers=headers, timeout=None)
    return client


@require_valid_token()
def search_item(project_code, zone, folder_relative_path, container_type='project'):
    token = UserConfig().access_token
    url = AppConfig.Connections.url_bff + '/v1/project/{}/search'.format(project_code)
    params = {
        'zone': zone,
        'project_code': project_code,
        'path': folder_relative_path,
        'container_type': container_type,
    }
    headers = {'Authorization': 'Bearer ' + token}
    res = requests.get(url, params=params, headers=headers)
    if res.status_code == 403:
        SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, project_code)
    elif res.status_code == 404:
        pass
    elif res.status_code == 401:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TOKEN, if_exit=True)
    elif res.status_code != 200:
        SrvErrorHandler.default_handle(res.text, True)

    return res.json()


@require_valid_token()
def get_attribute_template_by_id(template_id: str) -> Dict[str, Any]:
    token = UserConfig().access_token
    url = AppConfig.Connections.url_portal + f'/v1/data/manifest/{template_id}'
    headers = {'Authorization': 'Bearer ' + token}
    res = resilient_session().get(url, headers=headers)
    if res.status_code != 200:
        SrvErrorHandler.default_handle(res.text, True)

    return res.json().get('result', {})


@require_valid_token()
def get_file_info_by_geid(geid: list):
    token = UserConfig().access_token
    payload = {'geid': geid}
    headers = {'Authorization': 'Bearer ' + token}
    url = AppConfig.Connections.url_bff + '/v1/query/geid'
    res = resilient_session().post(url, headers=headers, json=payload)
    return res.json()['result']


@require_valid_token()
def check_item_duplication(item_list: List[str], zone: int, project_code: str) -> List[str]:
    '''
    Summary:
        Check if the item already exists in the project in batch.
    Parameters:
        - item_list: list of item path to check
        - zone: zone of the project
        - project_code: project code
    Returns:
        - list of item path that already exists in the project
    '''

    # url = AppConfig.Connections.url_base + '/portal/v1/files/exists'
    url = 'http://localhost:5060/v1/files/exists'
    headers = {'Authorization': 'Bearer ' + UserConfig().access_token}
    payload = {
        'locations': item_list,
        'container_code': project_code,
        'container_type': 'project',
        'zone': zone,
    }
    response = resilient_session().post(url, json=payload, headers=headers)
    if response.status_code != 200:
        SrvErrorHandler.default_handle(response.text, True)

    return response.json().get('result')


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
    if contain_invalid_char or len(folder_name) > 100 or not folder_name:
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


def identify_target_folder(project_path: str) -> Tuple[str, ItemType, str]:
    '''
    Summary:
        the function will validate if input folder path doesn't
        contain invalid characters and return the project code and target folder
    Parameters:
        - project_path:
            - for project folder the input folder path (eg. <project_code>/shared/<folder_name>)
            - for name folder the input folder path will be (eg. <project_code>/users/<folder_name>)
    Return:
        - project_code: the project code
        - folder_type: the folder type
        - target_folder: the target folder
    '''
    # split into project_code, folder_type, folder
    temp_paths = project_path.split('/', 2)
    project_code, folder_type, folder_name = temp_paths[0], '', ''

    # check folder type if is project folder or name folder
    # there will be a extra string for project folder between project code and folder name
    if len(temp_paths) >= 3:
        folder_type = ItemType.get_type_from_keyword(temp_paths[1])
        folder_name = temp_paths[2]
    else:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_NAMEFOLDER, True)
        target_folder = ''

    # first check if folder names are valid
    target_folder = '/'.join(folder_name.split('/'))
    for f in target_folder.split('/'):
        f = f.strip(' ')
        valid = validate_folder_name(f)
        if not valid:
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_FOLDERNAME, True)

    return project_code, folder_type, target_folder


def batch_generator(iterable: List[Any], batch_size=1):
    max_size = len(iterable)
    for start_index in range(0, max_size, batch_size):
        yield iterable[start_index : min(start_index + batch_size, max_size)]


def remove_the_output_file(filepath: str) -> None:
    """Remove the output file after each successful operation to avoid confusion."""
    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass
    except OSError:
        logger.warning(f'Unable to remove "{filepath}".')
