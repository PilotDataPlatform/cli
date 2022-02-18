from .user_login_logout import user_login, check_is_login, check_is_active
from .token_manager import SrvTokenManager
from app.configs.user_config import UserConfig
from functools import wraps

def require_valid_token(azp=None):
    def decorate(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            check_is_login()
            token_mgr = SrvTokenManager()
            user_config = UserConfig()
            token_validation = token_mgr.check_valid(azp)
            def is_valid_callback():
                pass
            def need_login_callback():
                user_login(user_config.username, user_config.password)
            def need_refresh_callback():
                token_mgr.refresh(azp)
            def need_change_callback():
                token_mgr.change_token(azp)
            switch_case = {
                "0": is_valid_callback, 
                "1": need_refresh_callback,
                "2": need_login_callback,
                "3": need_change_callback,
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
