from app.models.service_meta_class import MetaService
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from ..user_authentication.decorator import require_valid_token
import requests
import json
import click
import app.services.logger_services.log_functions as logger
from app.services.output_manager.error_handler import SrvErrorHandler, ECustomizedError, customized_error_msg
from app.services.output_manager.message_handler import SrvOutPutHandler


class SrvProjectManager(metaclass=MetaService):
    def __init__(self, interactive=True):
        self.user = UserConfig()
        self.interactive = interactive

    @require_valid_token()
    def list_all(self, if_print=True):
        url = AppConfig.Connections.url_bff + "/v1/projects"
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                res_to_dict = response.json()['result']
                if if_print:
                    SrvOutPutHandler.project_list_header()
                    for project in res_to_dict:
                        project_code = str(project['code'])
                        project_name = str(project['name'])[0:37]+'...' if len(str(project['name']))>37 else str(project['name'])
                        SrvOutPutHandler.print_list_parallel(project_name, project_code)
                    SrvOutPutHandler.count_item('projects', res_to_dict)
                return res_to_dict
            elif response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.USER_DISABLED, True)
            else:
                SrvErrorHandler.default_handle(response.content, True)
        except Exception as e:
            SrvErrorHandler.default_handle(response.content, True)

    def get_project_id_by_code(self, code):
        project_list = self.list_all(False)
        project_found = [project for project in project_list if project['code'] == code]
        if not project_found and self.interactive:
            SrvErrorHandler.customized_handle(ECustomizedError.CODE_NOT_FOUND, True)
        elif not project_found and not self.interactive:
            return customized_error_msg(ECustomizedError.CODE_NOT_FOUND)
        else:
            project_found = project_found[0]
            return int(project_found['id'])

    def get_project_geid_by_code(self, code):
        project_list = self.list_all(False)
        project_found = [project for project in project_list if project['code'] == code]
        if not project_found and self.interactive:
            SrvErrorHandler.customized_handle(ECustomizedError.CODE_NOT_FOUND, True)
        elif not project_found and not self.interactive:
            return False, customized_error_msg(ECustomizedError.CODE_NOT_FOUND)
        else:
            project_found = project_found[0]
            return True, str(project_found['geid'])
