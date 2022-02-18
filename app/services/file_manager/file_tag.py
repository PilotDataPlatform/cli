import requests
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.user_authentication.decorator import require_valid_token
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler, customized_error_msg
import app.services.logger_services.log_functions as logger

class SrvFileTag(metaclass=MetaService):
    appconfig =  AppConfig()
    user = UserConfig()

    def __init__(self, interactive=True):
        self.interactive = interactive

    @require_valid_token()
    def validate_tag(self, tags, container_id):
        payload = {"taglist": tags}
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
        }
        url = self.appconfig.Connections.url_file_tag + '/' + str(container_id) + '/tags/validate'
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code != 200:
            error_result = res.json()['error_msg'].upper().replace('-', 'to').replace(',', '').replace(' ', '_')
            _validation_error = getattr(ECustomizedError, error_result)
            if self.interactive:
                SrvErrorHandler.customized_handle(_validation_error, True)
            else:
                error = customized_error_msg(_validation_error)
                return False, error
        else:
            return True, res.json()

    @require_valid_token()
    def add_tag(self, tags: list, geid: str, container_id):
        payload = {"taglist": tags, "geid": geid}
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
        }
        url = self.appconfig.Connections.url_file_tag + '/' + str(container_id) + '/tags'
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            result = res.json()['result']
            return True, result
        else:
            error_result = res.json()['error_msg'].upper().replace(' ', '_')
            _validation_error = getattr(ECustomizedError, error_result)
            if self.interactive:
                SrvErrorHandler.customized_handle(_validation_error, True)
            else:
                error = customized_error_msg(_validation_error)
                return False, error
