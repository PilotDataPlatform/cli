# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from typing import Any
from typing import Dict
from typing import List
from uuid import UUID

from app.configs.app_config import AppConfig
from app.services.clients.base_auth_client import BaseAuthClient
from app.utils.aggregated import get_zone


class FileTrashClient(BaseAuthClient):
    '''
    Summary:
        A client for moving files to trash or directly deleting files permanently.
    '''

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
        self.zone = get_zone(zone) if zone else AppConfig.Env.green_zone

        self.endpoint = AppConfig.Connections.url_bff + '/v1'

    def move_to_trash(self) -> Dict[str, Any]:
        '''
        Summary:
            Move files to trash bin.
        '''
        params = {
            'target_ids': self.object_ids,
            'source_id': self.project_code,
            'zone': self.zone,
        }
        response = self.client.delete(f'{self.endpoint}/{self.project_code}/file', json=params)

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
        response = self.client.delete(f'{self.endpoint}/{self.project_code}/file/purge', json=params)

        return response.json()
