# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from httpx import HTTPStatusError

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.message_handler import SrvOutPutHandler

from ..user_authentication.decorator import require_valid_token


class SrvDatasetListManager(BaseAuthClient, metaclass=MetaService):
    def __init__(self, interactive=True):
        super().__init__(AppConfig.Connections.url_bff)

        self.user = UserConfig()
        self.interactive = interactive
        self.endpoint = AppConfig.Connections.url_bff + '/v1'

    @require_valid_token()
    def list_datasets(self, page, page_size) -> Tuple[List[Dict[str, Any]], int]:
        params = {'page': page, 'page_size': page_size}
        try:
            response = self._get('datasets', params=params)
        except HTTPStatusError as e:
            response = e.response
            if response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.USER_DISABLED, True)
            elif response.status_code == 401:
                SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TOKEN, if_exit=True)
            else:
                SrvErrorHandler.default_handle(response.content, True)

        res = response.json()
        res_to_dict = res.get('result')
        if self.interactive:
            SrvOutPutHandler.print_list_header('Dataset Title', 'Dataset Code')
            for dataset in res_to_dict:
                dataset_code = str(dataset['code'])
                if len(str(dataset['title'])) > 37:
                    dataset_name = str(dataset['title'])[0:37] + '...'
                else:
                    dataset_name = str(dataset['title'])
                SrvOutPutHandler.print_list_parallel(dataset_name, dataset_code)
            SrvOutPutHandler.count_item(page, 'datasets', res_to_dict, res.get('total'))
        return res_to_dict, res.get('total')
