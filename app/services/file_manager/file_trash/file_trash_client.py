# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import time
from typing import Any
from typing import Dict
from typing import List
from uuid import UUID

from app.configs.app_config import AppConfig
from app.models.item import ItemStatus
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.output_manager import message_handler
from app.utils.aggregated import get_file_info_by_geid
from app.utils.aggregated import get_zone


class FileTrashClient(BaseAuthClient):
    '''
    Summary:
        A client for moving files to trash or directly deleting files permanently.
    '''

    # for long pulling status check
    status_interval = 2
    max_status_check = 10

    def __init__(self, project_code: str, parent_id: UUID, object_ids: List[UUID], zone: str):
        '''
        Summary:
            Initialize file trash client.
        Parameters:
            project_code (str): project code.
            object_path (str): object path.
            zone (str): zone.
        '''
        super().__init__(AppConfig.Connections.url_bff)
        self.project_code = project_code
        self.object_ids = object_ids
        self.parent_id = parent_id
        self.zone = get_zone(zone)

        self.endpoint = self.endpoint + '/v1'

    def move_to_trash(self) -> Dict[str, Any]:
        '''
        Summary:
            Move files to trash bin.
        '''
        params = {
            'target_ids': self.object_ids,
            'source_id': self.parent_id,
            'zone': self.zone,
        }
        response = self._delete(f'{self.project_code}/files', params=params)

        return response.json()

    def permanently_delete(self) -> Dict[str, Any]:
        '''
        Summary:
            Permanently delete files from trash bin.
        '''
        params = {
            'target_ids': self.object_ids,
            'zone': self.zone,
        }
        response = self._delete(f'{self.project_code}/files/purge', params=params)

        return response.json()

    def check_status(self, status: ItemStatus) -> List[str]:
        '''
        Summary:
            use long pulling to check if the files are trashed or deleted.
            the status should be TRASHED or DELETED.
        Returns:
            - list of failed file paths
        '''

        id_check_list = self.object_ids
        message_handler.SrvOutPutHandler.trash_delete_in_progress(status)
        for _ in range(self.max_status_check):
            time.sleep(self.status_interval)

            next_check_list, in_progres = [], []
            item_info = get_file_info_by_geid(id_check_list)

            # take out the items which status is not the desired one for next round
            # result will be empty if item get trashed or deleted
            for item in item_info:
                item = item.get('result', {})
                if item.get('status') != status.value:
                    next_check_list.append(item.get('id'))
                    parent_path = item.get('parent_path') if status == ItemStatus.TRASHED else item.get('restore_path')
                    in_progres.append(parent_path + '/' + item.get('name'))

            id_check_list = next_check_list
            if len(id_check_list) == 0:
                break

        return in_progres
