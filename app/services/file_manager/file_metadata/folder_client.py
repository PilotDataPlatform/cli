# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import uuid

from httpx import HTTPStatusError

from app.configs.app_config import AppConfig
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.output_manager import message_handler
from app.services.output_manager.error_handler import SrvErrorHandler
from app.utils.aggregated import check_item_duplication
from app.utils.aggregated import search_item


class FolderClient(BaseAuthClient):
    def __init__(self, project_code: str, zone: str) -> None:
        super().__init__(AppConfig.Connections.url_bff + '/v1')

        self.project_code = project_code
        self.zone = {'greenroom': 0, 'core': 1}.get(zone)

    def _get_root_folder_id(self, root_folder: str) -> str:
        # get the current exist name folder or shared folder for reference
        exist_parent = root_folder
        exist_parent_item = search_item(self.project_code, self.zone, exist_parent).get('result')
        exist_parent_id = exist_parent_item.get('id')
        if not exist_parent_id:
            SrvErrorHandler.default_handle(f'Parent folder: {exist_parent} not exist', True)

        return exist_parent_id

    def create_folder(self, folder_path: str) -> dict:
        """Create object path is not on platfrom.

        it will create every non-exist folder along path.
        """

        path_list = folder_path.split('/')

        # first check every folder in path exist or not
        # the loop start with index 1 since we assume cli will not
        # create any name folder or project folder
        check_list = []
        for index in range(2, len(path_list)):
            check_list.append('/'.join(path_list[: index + 1]))
        if len(check_list) == 0:
            return {}

        # confirm if user want to create folder or not
        exist_path = check_item_duplication(check_list, self.zone, self.project_code)
        not_exist_path = sorted(set(check_list) - set(exist_path))
        if not not_exist_path:
            message_handler.SrvOutPutHandler.folder_duplicate_error(self.project_code, folder_path)
            exit(1)

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
