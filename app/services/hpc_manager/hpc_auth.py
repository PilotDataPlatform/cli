# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from app.configs.app_config import AppConfig
from app.models.service_meta_class import HPCMetaService
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import resilient_session


class HPCTokenManager(metaclass=HPCMetaService):
    def __init__(self, token):
        self.token = token

    @require_valid_token()
    def auth_user(self, host, username, password):
        url = AppConfig.Connections.url_bff + '/v1/hpc/auth'
        payload = {'token_issuer': host, 'username': username, 'password': password}
        headers = {'Authorization': 'Bearer ' + self.token}
        res = resilient_session().post(url, headers=headers, json=payload)
        _res = res.json()
        code = _res.get('code')
        if code == 200:
            token = _res.get('result')
            return token
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_AUTH_HPC, True)
