# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from typing import Tuple

import click
import questionary
from httpx import HTTPStatusError

import app.services.logger_services.log_functions as logger
from app.configs.app_config import AppConfig
from app.models.item import ItemStatus
from app.models.item import ItemType
from app.models.service_meta_class import MetaService
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import fit_terminal_width


class SrvFileList(BaseAuthClient, metaclass=MetaService):
    def __init__(self):
        super().__init__(AppConfig.Connections.url_bff)

        self.endpoint = AppConfig.Connections.url_bff + '/v1'
        self.zone_map = {
            0: AppConfig.Env.green_zone,
            1: AppConfig.Env.core_zone,
        }

    @require_valid_token()
    def list_files(self, paths: str, zone: str, page: int, page_size: int) -> Tuple[str, int]:
        # path is formatted as <project_code>/<root_folder>/<folder1>
        # split the path in to project_code, root_folder, and folder1
        project_path = paths.strip('/').split('/')
        project_code, source_type = project_path[0], 'project'
        folder_rel_path = '/'.join(project_path[1:])
        root_folder = ItemType.ROOTFOLDER
        if len(project_path) > 1:
            root_folder = ItemType.get_type_from_keyword(project_path[1])
            folder_rel_path = folder_rel_path.replace(project_path[1], root_folder.get_prefix_by_type()[:-1], 1)
            folder_rel_path = folder_rel_path.lstrip('/')

        # now query the backend to get the file list
        status = ItemStatus.TRASHED if root_folder == ItemType.TRASH else ItemStatus.ACTIVE
        zone = '' if root_folder == ItemType.TRASH else zone
        params = {
            'project_code': project_code,
            'source_type': source_type,
            'folder': folder_rel_path,
            'zone': zone,
            'page': page,
            'page_size': page_size,
            'status': str(status),
        }
        try:
            response = self._get(f'{project_code}/files/query', params=params)
            res_json = response.json()
        except HTTPStatusError as e:
            response = e.response
            res_json = response.json()
            if response.status_code == 403 and res_json.get('error_msg') != 'Folder not exist':
                SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, True)
            elif res_json.get('error_msg') == 'Folder not exist':
                SrvErrorHandler.customized_handle(ECustomizedError.INVALID_FOLDER, True)

        res = res_json.get('result')
        # then format the console output
        files, folders = '', ''
        for f in res:
            item_type = ItemType(f.get('type'))
            # if there is space within the nane add double quotation to aviod confusion
            if ' ' in f.get('name'):
                f['name'] = f'"{f.get("name")}"'

            # formating zone info for trashed items
            if f.get('status') == ItemStatus.TRASHED:
                zone = AppConfig.Env.zone_int2string.get(f.get('zone'))
                f['name'] = f'{f.get("name")}({zone})'

            if item_type == ItemType.FILE:
                files = files + f.get('name') + ' ...'
            else:
                folders = folders + f"\033[34m{f.get('name')}\033[0m ..."

        f_string = folders + files
        return f_string, res_json.get('total')

    def list_files_without_pagination(self, paths, zone, page, page_size):
        files, _ = self.list_files(paths, zone, page, page_size)
        query_result = fit_terminal_width(files)
        logger.info(query_result)

    def list_files_with_pagination(self, paths, zone, page, page_size):
        while True:
            files, total = self.list_files(paths, zone, page, page_size)
            file_list = files.split('...')[:-1] if files != '' else []
            query_result = fit_terminal_width(files)
            logger.info(query_result)

            if total < AppConfig.Env.interative_threshold:
                break
            elif len(file_list) < page_size and page == 0:
                choice = ['exit']
            elif len(file_list) < page_size and page != 0:
                choice = ['previous page', 'exit']
            elif page == 0:
                choice = ['next page', 'exit']
            else:
                choice = ['previous page', 'next page', 'exit']
            val = questionary.select('\nWhat do you want?', qmark='', choices=choice).ask()
            if val == 'exit':
                break
            elif val == 'next page':
                click.clear()
                page += 1
            elif val == 'previous page':
                click.clear()
                page -= 1
