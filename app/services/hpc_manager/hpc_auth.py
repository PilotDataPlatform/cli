from os import access
from app.services.user_authentication.decorator import require_valid_token
from app.models.service_meta_class import HPCMetaService
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
import requests
import app.services.logger_services.log_functions as logger
from app.services.output_manager.error_handler import SrvErrorHandler, ECustomizedError, customized_error_msg
from app.services.user_authentication.user_login_logout import user_login, check_is_login, check_is_active
from app.services.output_manager.message_handler import SrvOutPutHandler


class HPCTokenManager(metaclass=HPCMetaService):
    def __init__(self, token):
        self.token = token

    @require_valid_token()
    def auth_user(self, host, username, password):
        url = AppConfig.Connections.url_bff + '/v1/hpc/auth'
        payload = {
            "token_issuer": host,
            "username": username,
            "password": password
        }
        headers = {'Authorization': 'Bearer ' + self.token}
        res = requests.post(url, headers=headers, json=payload)
        _res = res.json()
        code = _res.get('code')
        if code == 200:
            token = _res.get('result')
            return token
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_AUTH_HPC, True)
