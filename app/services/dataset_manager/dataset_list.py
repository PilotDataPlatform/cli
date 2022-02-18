from app.models.service_meta_class import MetaService
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from ..user_authentication.decorator import require_valid_token
import requests
import click
import app.services.logger_services.log_functions as logger
from app.services.output_manager.error_handler import SrvErrorHandler, ECustomizedError
from app.services.output_manager.message_handler import SrvOutPutHandler


class SrvDatasetListManager(metaclass=MetaService):
    def __init__(self, interactive=True):
        self.user = UserConfig()
        self.interactive = interactive

    @require_valid_token()
    def list_datasets(self, if_print=True):
        url = AppConfig.Connections.url_bff + '/v1/datasets'
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                res_to_dict = response.json()['result']
                if if_print:
                    SrvOutPutHandler.dataset_list_header()
                    for dataset in res_to_dict:
                        dataset_code = str(dataset['code'])
                        dataset_name = str(dataset['title'])[0:37]+'...' if len(str(dataset['title']))>37 else str(dataset['title'])
                        SrvOutPutHandler.print_list_parallel(dataset_name, dataset_code)
                    SrvOutPutHandler.count_item('datasets', res_to_dict)
                return res_to_dict
            elif response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.USER_DISABLED, True)
            else:
                SrvErrorHandler.default_handle(response.content, True)
        except Exception as e:
            SrvErrorHandler.default_handle(response.content, True)