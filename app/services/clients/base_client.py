# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import logging
import time
from typing import Any
from typing import Mapping
from typing import Optional

from httpx import Client
from httpx import RequestError
from httpx import Response

from app.configs.config import ConfigClass
from app.configs.user_config import UserConfig

logger = logging.getLogger('pilot.cli.base_client')


class BaseClient:
    """Client for any inherited service clients."""

    user = UserConfig()

    def __init__(self, endpoint: str, timeout: int = 10) -> None:
        self.endpoint_v1 = f'{endpoint}/v1'
        self.client = Client(timeout=timeout)
        self.headers = {'Authorization': 'Bearer ' + self.user.access_token, 'VM-Info': ConfigClass.vm_info}
        self.retry_status = [401, 503]
        self.retry_count = 3
        self.retry_interval = 0.1

    def _request(
        self, method: str, url: str, json: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None
    ) -> Response:
        """Send request."""
        try:
            url = f'{self.endpoint_v1}/{url}'
            for _ in range(self.retry_count):
                response = self.client.request(method, url, json=json, params=params, headers=self.headers)
                if response.status_code not in self.retry_status:
                    break
                logger.info(f'Request "{method} {url}" and params {params} received status {response.status_code}.')
                time.sleep(self.retry_interval)
        except RequestError:
            message = f'Unable to query data from auth service with url "{method} {url}" and params "{params}".'
            logger.exception(message)
            raise Exception(message)

        return response

    def _get(self, url: str, params: Optional[Mapping[str, Any]] = None) -> Response:
        """Send GET request."""
        return self._request('GET', url, params=params)

    def _post(self, url: str, json: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None) -> Response:
        """Send POST request."""
        return self._request('POST', url, json=json, params=params)

    def _put(self, url: str, json: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None) -> Response:
        """Send PUT request."""
        return self._request('PUT', url, json=json, params=params)

    def _delete(self, url: str, params: Optional[Mapping[str, Any]] = None, json: Optional[Any] = None) -> Response:
        """Send DELETE request."""
        return self._request('DELETE', url, params=params, json=json)

    def _patch(self, url: str, json: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None) -> Response:
        """Send PATCH request."""
        return self._request('PATCH', url, json=json, params=params)
