# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import logging
from typing import Any
from typing import Mapping
from typing import Optional

from httpx import Client
from httpx import RequestError
from httpx import Response

from app.configs.config import ConfigClass

logger = logging.getLogger('pilot.cli.base_client')


class BaseClient:
    """Client for any inherited service clients."""

    def __init__(self, endpoint: str, timeout: int) -> None:
        self.endpoint_v1 = f'{endpoint}/v1'
        self.client = Client(headers={'VM-Info': ConfigClass.vm_info}, timeout=timeout)

    async def _request(
        self, method: str, url: str, json: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None
    ) -> Response:
        """Make http request."""

        try:
            response = await self.client.request(method, url, json=json, params=params)
            logger.info(f'Request "{method} {url}" and params {params} received status {response.status_code}.')
        except RequestError:
            message = f'Unable to query data from auth service with url "{method} {url}" and params "{params}".'
            logger.exception(message)
            raise Exception(message)

        return response

    async def _get(self, url: str, params: Optional[Mapping[str, Any]] = None) -> Response:
        """Send GET request."""

        return await self._request('GET', url, params=params)

    async def _post(self, url: str, json: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None) -> Response:
        """Send POST request."""

        return await self._request('POST', url, json=json, params=params)

    async def _put(self, url: str, json: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None) -> Response:
        return await self._request('PUT', url, json=json, params=params)

    async def _delete(
        self, url: str, params: Optional[Mapping[str, Any]] = None, json: Optional[Any] = None
    ) -> Response:
        """Send DELETE request."""

        return await self._request('DELETE', url, params=params, json=json)

    async def _patch(
        self, url: str, json: Optional[Any] = None, params: Optional[Mapping[str, Any]] = None
    ) -> Response:
        """Send PATCH request."""

        return await self._request('PATCH', url, json=json, params=params)
