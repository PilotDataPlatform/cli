# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.message_handler import SrvOutPutHandler
from app.utils.aggregated import resilient_session

from ..user_authentication.decorator import require_valid_token


class SrvDatasetListManager(metaclass=MetaService):
    def __init__(self, interactive=True):
        self.user = UserConfig()
        self.interactive = interactive

    @require_valid_token()
    def list_datasets(self, page, page_size, filter_by_creator: bool = True):
        url = AppConfig.Connections.url_bff + '/v1/datasets'
        headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
        }
        params = {'page': page, 'page_size': page_size}
        if filter_by_creator:
            params['creator'] = self.user.username
        try:
            response = resilient_session().get(url, headers=headers, params=params)
            if response.status_code == 200:
                res_to_dict = response.json()['result']
                if self.interactive:
                    SrvOutPutHandler.print_list_header('Dataset Title', 'Dataset Code')
                    for dataset in res_to_dict:
                        dataset_code = str(dataset['code'])
                        if len(str(dataset['title'])) > 37:
                            dataset_name = str(dataset['title'])[0:37] + '...'
                        else:
                            dataset_name = str(dataset['title'])
                        SrvOutPutHandler.print_list_parallel(dataset_name, dataset_code)
                    SrvOutPutHandler.count_item(page, 'datasets', res_to_dict)
                return res_to_dict
            elif response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.USER_DISABLED, True)
            else:
                SrvErrorHandler.default_handle(response.content, True)
        except Exception as e:
            SrvErrorHandler.default_handle(f'Error: {str(e)}', True)
