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

logger = logging.getLogger('pilot.cli.base_client')


class BaseClient:
    """Client for any inherited service clients."""

    def __init__(self, endpoint: str, timeout: int = 10) -> None:
        self.endpoint = endpoint
        self.client = Client(timeout=timeout)
        self.headers = {'VM-Info': ConfigClass.vm_info}
        self.retry_status = [401, 503]
        self.retry_count = 3
        self.retry_interval = 0.1

    def _request(
        self,
        method: str,
        url: str,
        json: Optional[Any] = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, Any]] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> Response:
        """Send request with retry."""

        for _ in range(self.retry_count):
            response = self._single_request(method, url, json, params, headers, data)
            if response.status_code not in self.retry_status:
                response.raise_for_status()
                return response
            time.sleep(self.retry_interval)

        logger.debug(f'failed with over {self.retry_count} retries.')

        response.raise_for_status()
        return None

    def _single_request(
        self,
        method: str,
        url: str,
        json: Optional[Any] = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, Any]] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> Response:
        """Send request."""
        try:
            url = f'{self.endpoint}/{url}'
            if headers:
                self.headers.update(headers)

            response = self.client.request(method, url, json=json, params=params, headers=self.headers, data=data)
        except RequestError:
            message = f'Unable to query data with url "{method} {url}".'
            logger.exception(message)
            raise Exception(message)

        return response

    def _get(
        self, url: str, params: Optional[Mapping[str, Any]] = None, headers: Optional[Mapping[str, Any]] = None
    ) -> Response:
        """Send GET request."""
        return self._request('GET', url, params=params, headers=headers)

    def _post(
        self,
        url: str,
        json: Optional[Any] = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, Any]] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> Response:
        """Send POST request."""
        return self._request('POST', url, json=json, params=params, headers=headers, data=data)

    def _put(
        self,
        url: str,
        json: Optional[Any] = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, Any]] = None,
        data: Optional[Mapping[str, Any]] = None,
    ) -> Response:
        """Send PUT request."""
        return self._request('PUT', url, json=json, params=params, headers=headers, data=data)

    def _delete(self, url: str, params: Optional[Mapping[str, Any]] = None, json: Optional[Any] = None) -> Response:
        """Send DELETE request."""
        return self._request('DELETE', url, params=params, json=json)

    def _patch(
        self,
        url: str,
        json: Optional[Any] = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, Any]] = None,
    ) -> Response:
        """Send PATCH request."""
        return self._request('PATCH', url, json=json, params=params)
