# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from typing import Dict
from typing import Tuple

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.message_handler import SrvOutPutHandler

from ..user_authentication.decorator import require_valid_token


class SrvProjectManager(BaseAuthClient, metaclass=MetaService):
    def __init__(self, interactive=True):
        super().__init__(AppConfig.Connections.url_bff)

        self.user = UserConfig()
        self.interactive = interactive
        self.endpoint = AppConfig.Connections.url_bff + '/v1'

    @require_valid_token()
    def list_projects(self, page, page_size, order, order_by) -> Tuple[Dict, int]:
        params = {'page': page, 'page_size': page_size, 'order': order, 'order_by': order_by}
        try:
            response = self._get('projects', params=params)
            if response.status_code == 200:
                res_to_dict = response.json().get('result')
                total = response.json().get('total')
                if self.interactive:
                    SrvOutPutHandler.print_list_header('Project Name', 'Project Code')
                    for project in res_to_dict:
                        project_code = str(project['code'])
                        if len(str(project['name'])) > 37:
                            project_name = str(project['name'])[0:37] + '...'
                        else:
                            project_name = str(project['name'])
                        SrvOutPutHandler.print_list_parallel(project_name, project_code)
                    SrvOutPutHandler.count_item(page, 'projects', res_to_dict, total)
                return res_to_dict, total
            elif response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.USER_DISABLED, True)
            else:
                SrvErrorHandler.default_handle(response.content, True)
        except Exception:
            SrvErrorHandler.default_handle('Error when listing projects', True)
