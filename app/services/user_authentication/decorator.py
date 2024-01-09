# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from functools import wraps

from app.configs.config import ConfigClass
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.token_manager import SrvTokenManager
from app.services.user_authentication.user_login_logout import check_is_active
from app.services.user_authentication.user_login_logout import check_is_login


def require_valid_token(azp=ConfigClass.keycloak_device_client_id):
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
