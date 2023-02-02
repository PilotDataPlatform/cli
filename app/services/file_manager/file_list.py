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

import click
import questionary
import requests

import app.services.logger_services.log_functions as logger
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import fit_terminal_width
from app.utils.aggregated import search_item


class SrvFileList(metaclass=MetaService):
    user = UserConfig()

    @require_valid_token()
    def list_files(self, paths, zone, page, page_size):
        project_path = paths.strip('/').split('/')
        project_code = project_path[0]
        folder_rel_path = '/'.join(project_path[1:])
        if len(project_path) == 1:
            source_type = 'project'
        else:
            source_type = 'project'
            res = search_item(project_code, zone, folder_rel_path, 'folder')
        get_url = AppConfig.Connections.url_bff + f'/v1/{project_code}/files/query'
        headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
        }
        params = {
            'project_code': project_code,
            'folder': folder_rel_path,
            'source_type': source_type,
            'zone': zone,
            'page': page,
            'page_size': page_size,
        }
        response = requests.get(get_url, params=params, headers=headers)
        res_json = response.json()
        if res_json.get('code') == 403 and res_json.get('error_msg') != 'Folder not exist':
            SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, True)
        elif res_json.get('error_msg') == 'Folder not exist':
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_FOLDER, True)
        res = res_json.get('result')
        files = ''
        folders = ''
        for f in res:
            if 'file' == f.get('type'):
                files = files + f.get('name') + ' ...'
            elif f.get('type') in ['folder', 'name_folder']:
                folders = folders + f"\033[34m{f.get('name')}\033[0m ..."
        f_string = folders + files
        return f_string

    def list_files_without_pagination(self, paths, zone, page, page_size):
        files = self.list_files(paths, zone, page, page_size)
        query_result = fit_terminal_width(files)
        logger.info(query_result)

    def list_files_with_pagination(self, paths, zone, page, page_size):
        while True:
            files = self.list_files(paths, zone, page, page_size)
            if len(files) < page_size and page == 0:
                break
            elif len(files) < page_size and page != 0:
                choice = ['previous page', 'exit']
            elif page == 0:
                choice = ['next page', 'exit']
            else:
                choice = ['previous page', 'next page', 'exit']
            query_result = fit_terminal_width(files)
            logger.info(query_result)
            val = questionary.select('\nWhat do you want?', qmark='', choices=choice).ask()
            if val == 'exit':
                break
            elif val == 'next page':
                click.clear()
                page += 1
            elif val == 'previous page':
                click.clear()
                page -= 1
