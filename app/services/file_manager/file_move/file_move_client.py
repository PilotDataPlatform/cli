# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import uuid
from sys import exit

import click
from click import Abort

import app.services.output_manager.message_handler as message_handler
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.error_handler import customized_error_msg
from app.utils.aggregated import resilient_session
from app.utils.aggregated import search_item


class FileMoveClient:
    """
    Summary:
        A client for interacting with file metadata. currently support to download
        file metadata from metadata service.
    """

    def __init__(
        self,
        zone: str,
        project_code: str,
        src_item_path: str,
        dest_item_path: str,
    ) -> None:
        """
        Summary:
            Initialize file move client.
        Parameters:
            zone (str): zone.
            project_code (str): project code.
            src_item_path (str): source item path.
            dest_item_path (str): destination item path.
        """

        self.zone = zone
        self.project_code = project_code
        self.src_item_path = src_item_path
        self.dest_item_path = dest_item_path

        self.user = UserConfig()

    def create_object_path_if_not_exist(self, folder_path: str) -> dict:
        """Create object path is not on platfrom.

        it will create every non-exist folder along path.
        """

        path_list = folder_path.split('/')
        # first check every folder in path exist or not
        # the loop start with index 1 since we assume cli will not
        # create any name folder or project folder
        check_list = []
        for index in range(1, len(path_list) - 1):
            check_list.append('/'.join(path_list[: index + 1]))
        if len(check_list) == 0:
            return

        url = AppConfig.Connections.url_base + '/portal/v1/files/exists'
        zone_int = {'greenroom': 0, 'core': 1}.get(self.zone.lower())
        headers = {'Authorization': 'Bearer ' + UserConfig().access_token}
        payload = {
            'locations': check_list,
            'container_code': self.project_code,
            'container_type': 'project',
            'zone': zone_int,
        }
        response = resilient_session().post(url, json=payload, headers=headers)
        if response.status_code != 200:
            SrvErrorHandler.default_handle(response.text, True)

        # confirm if user want to create folder or not
        exist_path = response.json().get('result')
        not_exist_path = sorted(set(check_list) - set(exist_path))
        if not_exist_path:
            try:
                click.confirm(customized_error_msg(ECustomizedError.CREATE_FOLDER_IF_NOT_EXIST), abort=True)
            except Abort:
                message_handler.SrvOutPutHandler.move_cancelled()
                exit(1)
        else:
            return

        # get the current exist parent folder for reference
        exist_parent = not_exist_path[0].rsplit('/', 1)[0]
        exist_parent_item = search_item(self.project_code, self.zone, exist_parent).get('result')
        exist_parent_id = exist_parent_item.get('id')
        to_create = {'folders': [], 'parent_id': exist_parent_id}
        for path in not_exist_path:
            parent_path, folder_name = path.rsplit('/', 1)
            current_item_id = str(uuid.uuid4())
            to_create['folders'].append(
                {
                    'name': folder_name,
                    'parent': exist_parent_id,
                    'parent_path': parent_path,
                    'container_code': self.project_code,
                    'container_type': 'project',
                    'zone': zone_int,
                    'item_id': current_item_id,
                }
            )
            exist_parent_id = current_item_id

        url = AppConfig.Connections.url_bff + '/v1/folders/batch'
        headers = {'Authorization': 'Bearer ' + UserConfig().access_token}
        response = resilient_session().post(url, json=to_create, headers=headers)
        if response.status_code != 200:
            SrvErrorHandler.default_handle(response.text, True)
        return response.json().get('result')

    def move_file(self) -> None:
        """
        Summary:
            Move file.
        """

        self.create_object_path_if_not_exist(self.dest_item_path)

        try:
            url = AppConfig.Connections.url_bff + f'/v1/{self.project_code}/files'
            payload = {
                'src_item_path': self.src_item_path,
                'dest_item_path': self.dest_item_path,
                'zone': self.zone,
            }
            headers = {'Authorization': 'Bearer ' + self.user.access_token, 'Session-ID': self.user.session_id}

            response = resilient_session().patch(url, json=payload, headers=headers, timeout=None)
            response.raise_for_status()

            return response.json().get('result')
        except Exception:
            if response.status_code == 422:
                error_message = ''
                for x in response.json().get('detail'):
                    error_message += '\n' + x.get('msg')
            else:
                error_message = response.json().get('error_msg')
            message_handler.SrvOutPutHandler.move_action_failed(self.src_item_path, self.dest_item_path, error_message)
            exit(1)
