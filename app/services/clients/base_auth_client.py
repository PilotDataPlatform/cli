# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import time
from typing import Any
from typing import Mapping

from requests import Response

from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig
from app.services.clients.base_client import BaseClient
from app.services.user_authentication.token_manager import SrvTokenManager


class BaseAuthClient(BaseClient):

    token_manager: SrvTokenManager
    user = UserConfig()

    def __init__(self, endpoint: str, timeout: int = 10) -> None:
        super().__init__(endpoint, timeout)

        self.token_manager = SrvTokenManager()
        self.headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
            'VM-Info': ConfigClass.vm_info,
            'Session-ID': self.user.session_id,
        }

    def _request(
        self,
        method: str,
        url: str,
        json: Any | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> Response:
        for _ in range(self.retry_count):
            response = self._single_request(method, url, json, params, headers, data)
            if response.status_code not in self.retry_status:
                response.raise_for_status()
                return response
            time.sleep(self.retry_interval)

            if response.status_code == 401:
                self.token_manager.refresh(ConfigClass.keycloak_device_client_id)
                self.headers['Authorization'] = 'Bearer ' + self.user.access_token

        response.raise_for_status()
        return None
