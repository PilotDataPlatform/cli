# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import uuid
from sys import exit

import click
from click import Abort
from httpx import HTTPStatusError

import app.services.output_manager.message_handler as message_handler
from app.configs.app_config import AppConfig
from app.models.item import ItemType
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.error_handler import customized_error_msg
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import check_item_duplication
from app.utils.aggregated import search_item


class FileMoveClient(BaseAuthClient):
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
        skip_confirm: bool = False,
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
        super().__init__(AppConfig.Connections.url_bff)

        self.zone = {'greenroom': 0, 'core': 1}.get(zone)
        self.project_code = project_code
        self.src_item_path = src_item_path
        self.dest_item_path = dest_item_path
        self.skip_confirm = skip_confirm

        self.endpoint = AppConfig.Connections.url_bff + '/v1'

    def _get_root_folder_id(self, root_folder: str) -> str:
        # get the current exist parent folder for reference
        exist_parent = root_folder
        exist_parent_item = search_item(self.project_code, self.zone, exist_parent).get('result')
        exist_parent_id = exist_parent_item.get('id')
        if not exist_parent_id:
            SrvErrorHandler.default_handle(f'Parent folder: {exist_parent} not exist', True)

        return exist_parent_id

    def create_object_path_if_not_exist(self, folder_path: str) -> dict:
        """Create object path is not on platfrom.

        it will create every non-exist folder along path.
        """

        path_list = folder_path.split('/')

        # first check every folder in path exist or not
        # the loop start with index 1 since we assume cli will not
        # create any name folder or project folder
        check_list = []
        for index in range(2, len(path_list) - 1):
            check_list.append('/'.join(path_list[: index + 1]))
        if len(check_list) == 0:
            return

        # confirm if user want to create folder or not
        exist_path = check_item_duplication(check_list, self.zone, self.project_code)
        not_exist_path = sorted(set(check_list) - set(exist_path))
        if not_exist_path:
            try:
                if not self.skip_confirm:
                    click.confirm(customized_error_msg(ECustomizedError.CREATE_FOLDER_IF_NOT_EXIST), abort=True)
            except Abort:
                message_handler.SrvOutPutHandler.move_cancelled()
                exit(1)
        else:
            return

        exist_parent_id = self._get_root_folder_id(not_exist_path[0].rsplit('/', 1)[0])
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
                    'zone': self.zone,
                    'item_id': current_item_id,
                }
            )
            exist_parent_id = current_item_id

        try:
            response = self._post('folders/batch', json=to_create)
        except HTTPStatusError as e:
            response = e.response
            SrvErrorHandler.default_handle(response.text, True)

        return response.json().get('result')

    @require_valid_token()
    def move_file(self) -> None:
        """
        Summary:
            Move file.
        """

        # self.create_object_path_if_not_exist(self.dest_item_path)
        # similar to linux mv command, cli will check if destination is a folder or file
        # if file, it will raise error with duplicate
        # if folder, it will move the file into the folder
        # if detination is not exist, it will rename the item
        dest_item = search_item(self.project_code, self.zone, self.dest_item_path).get('result')
        if dest_item:
            if dest_item.get('type') == ItemType.FILE.value:
                item_name = dest_item.get('name')
                message_handler.SrvOutPutHandler.move_action_failed(
                    self.src_item_path, f'{self.dest_item_path}/{item_name}', f'Item {item_name} already exists'
                )
                exit(1)
            else:
                self.dest_item_path = f'{self.dest_item_path}/{self.src_item_path.split("/")[-1]}'
        else:
            # dest folder not exist, check if parent folder exist
            parent_path = self.dest_item_path.rsplit('/', 1)[0]
            parent_item = search_item(self.project_code, self.zone, parent_path).get('result')
            if not parent_item:
                message_handler.SrvOutPutHandler.move_action_failed(
                    self.src_item_path, self.dest_item_path, f'Parent folder {parent_path} not exist'
                )
                exit(1)

        try:
            payload = {
                'src_item_path': self.src_item_path,
                'dest_item_path': self.dest_item_path,
                'zone': self.zone,
            }
            response = self._patch(f'{self.project_code}/files', json=payload)

            return response.json().get('result')
        except HTTPStatusError as e:
            response = e.response
            if response.status_code == 422:
                error_message = ''
                for x in response.json().get('detail'):
                    error_message += '\n' + x.get('msg')
            elif response.status_code == 500:
                item_name = self.src_item_path.split('/')[-1]
                error_message = f'Item {item_name} already exists'
            else:
                error_message = response.json().get('error_msg')
            message_handler.SrvOutPutHandler.move_action_failed(self.src_item_path, self.dest_item_path, error_message)
            exit(1)
