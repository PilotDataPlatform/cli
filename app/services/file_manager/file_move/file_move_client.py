# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.utils.aggregated import resilient_session


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

    def move_file(self) -> None:
        """
        Summary:
            Move file.
        """

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
        except Exception as e:
            raise e
