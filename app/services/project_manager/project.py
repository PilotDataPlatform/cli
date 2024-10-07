# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import requests

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.message_handler import SrvOutPutHandler

from ..user_authentication.decorator import require_valid_token


class SrvProjectManager(metaclass=MetaService):
    def __init__(self, interactive=True):
        self.user = UserConfig()
        self.interactive = interactive

    @require_valid_token()
    def list_projects(self, page, page_size, order, order_by):
        url = AppConfig.Connections.url_bff + '/v1/projects'
        headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
        }
        params = {'page': page, 'page_size': page_size, 'order': order, 'order_by': order_by}
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                res_to_dict = response.json()['result']
                if self.interactive:
                    SrvOutPutHandler.print_list_header('Project Name', 'Project Code')
                    for project in res_to_dict:
                        project_code = str(project['code'])
                        if len(str(project['name'])) > 37:
                            project_name = str(project['name'])[0:37] + '...'
                        else:
                            project_name = str(project['name'])
                        SrvOutPutHandler.print_list_parallel(project_name, project_code)
                    SrvOutPutHandler.count_item(page, 'projects', res_to_dict)
                return res_to_dict
            elif response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.USER_DISABLED, True)
            else:
                SrvErrorHandler.default_handle(response.content, True)
        except Exception:
            SrvErrorHandler.default_handle(response.content, True)
