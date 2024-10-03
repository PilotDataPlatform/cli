# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import os
import re
import shutil
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from httpx import HTTPStatusError
from packaging.version import Version

import app.services.logger_services.log_functions as logger
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.item import ItemType
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.logger_services.debugging_log import debug_logger
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token


@require_valid_token()
def search_item(project_code, zone, folder_relative_path, container_type='project'):
    http_client = BaseAuthClient(AppConfig.Connections.url_bff)
    params = {
        'zone': zone,
        'project_code': project_code,
        'path': folder_relative_path,
        'container_type': container_type,
    }
    try:
        res = http_client._get(f'v1/project/{project_code}/search', params=params)
    except HTTPStatusError as e:
        res = e.response
        if res.status_code == 403:
            SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, project_code)
        elif res.status_code == 404:
            pass
        elif res.status_code == 401:
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TOKEN, if_exit=True)
        else:
            SrvErrorHandler.default_handle(res.text, True)

    return res.json()


@require_valid_token()
def get_attribute_template_by_id(template_id: str) -> Dict[str, Any]:
    http_client = BaseAuthClient(AppConfig.Connections.url_portal)
    try:
        res = http_client._get(f'v1/data/manifest/{template_id}')
    except HTTPStatusError as e:
        res = e.response
        SrvErrorHandler.default_handle(res.text, True)

    return res.json().get('result', {})


@require_valid_token()
def get_file_info_by_geid(geid: list):
    payload = {'geid': geid}
    http_client = BaseAuthClient(AppConfig.Connections.url_bff, timeout=60)
    try:

        start_time = time.time()
        res = http_client._post('v1/query/geid', json=payload)
        debug_logger.debug(f'Time taken to get file info: {time.time() - start_time}')
    except HTTPStatusError as e:
        res = e.response
        SrvErrorHandler.default_handle(res.text, True)

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

    httpx_client = BaseAuthClient(AppConfig.Connections.url_base)
    payload = {
        'locations': item_list,
        'container_code': project_code,
        'container_type': 'project',
        'zone': zone,
    }

    try:
        response = httpx_client._post('portal/v1/files/exists', json=payload)
    except HTTPStatusError as e:
        response = e.response
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
                    file = normalize_join(path, name)
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
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_PROJECT_PATH, True)
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


def get_latest_cli_version() -> Version:
    try:
        httpx_client = BaseAuthClient(AppConfig.Connections.url_download_greenroom)
        user_config = UserConfig()
        if not user_config.is_access_token_exists():
            return Version('0.0.0')

        response = httpx_client._get('v2/download/cli')
        result = response.json().get('result', {})
        latest_version = result.get('linux', {}).get('version', '0.0.0')

        return Version(latest_version)
    except (SystemExit, Exception):
        return Version('0.0.0')


def normalize_input_paths(options: list[str]):
    """the decorator to process windows file path into linux like path in windows all input is seperated by `\\` eg.

    .\\app\\configs\\user_config.py to normalize all path with current backend logic. This function will accept a list
    of options that will need to be replaced with `/`
    """

    def decorator(f):
        def wrapped(*args, **kwargs):
            for option in options:
                arg = kwargs.get(option)
                if arg is None:
                    new_arg = None
                elif isinstance(arg, tuple):
                    new_arg = tuple([x.replace('\\', '/') for x in arg])
                else:
                    new_arg = arg.replace('\\', '/')
                kwargs[option] = new_arg
            return f(*args, **kwargs)

        return wrapped

    return decorator


def normalize_join(*paths: str) -> str:
    """normalize os.path.join with linux style path. In windows system, the os.path.join will automaticall use \\ to
    connect two path. In order to align with current backend adding this function to unify the path creation.

    Parameter:
        - paths(str list): the path need to be joined

    Return:
        - (str): the joined path with forward slashes.
    """

    joined_path = os.path.join(*paths)
    normalized_path = joined_path.replace('\\', '/')
    return normalized_path
