# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
