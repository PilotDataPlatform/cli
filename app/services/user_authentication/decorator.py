# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from functools import wraps

from app.configs.app_config import AppConfig
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler

from .token_manager import SrvTokenManager
from .user_login_logout import check_is_active
from .user_login_logout import check_is_login
from .user_set_config import check_config


def require_valid_token(azp=AppConfig.Env.keycloak_device_client_id):
    def decorate(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            check_is_login()
            token_mgr = SrvTokenManager()
            token_validation = token_mgr.check_valid(azp)

            def is_valid_callback():
                pass

            def need_login_callback():
                SrvErrorHandler.customized_handle(ECustomizedError.LOGIN_SESSION_INVALID, True)

            def need_refresh_callback():
                token_mgr.refresh(azp)

            switch_case = {
                '0': is_valid_callback,
                '1': need_refresh_callback,
                '2': need_login_callback,
            }
            to_exe = switch_case.get(str(token_validation), is_valid_callback)
            to_exe()
            return func(*args, **kwargs)

        return decorated

    return decorate


def require_login_session(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        check_is_active()
        check_is_login()
        return func(*args, **kwargs)

    return decorated


def require_config(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        check_config()
        return func(*args, **kwargs)

    return decorated
