# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
    def list_datasets(self, page, page_size):
        url = AppConfig.Connections.url_bff + '/v1/datasets'
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
        }
        params = {
            'page': page,
            'page_size': page_size
        }
        try:
            response = resilient_session().get(url, headers=headers, params=params)
            if response.status_code == 200:
                res_to_dict = response.json()['result']
                if self.interactive:
                    SrvOutPutHandler.print_list_header("Dataset Title", "Dataset Code")
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
        except Exception:
            SrvErrorHandler.default_handle(response.content, True)
