# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import configparser
import os
import stat
import sys
import time
from pathlib import Path
from typing import Iterable
from typing import Union

from app.configs.config import ConfigClass
from app.models.singleton import Singleton
from app.services.crypto.crypto import decryption
from app.services.crypto.crypto import encryption
from app.services.crypto.crypto import generate_secret
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler


class UserConfig(metaclass=Singleton):
    """The class to maintain the user access/fresh token Note here: the base class is Singleton, meaning no matter how
    code initializes the class.

    This user config is global.
    """

    def __init__(
        self,
        config_path: Union[str, Path, None] = None,
        config_filename: Union[str, None] = None,
        is_cloud_mode: Union[bool, None] = None,
    ) -> None:
        """When `is_cloud_mode` is enabled, it omits the checks for file or folder ownership and correct access mode for
        the user.

        This adjustment is made to prevent complications with mounted NFS volumes where all files have root ownership.
        """

        if config_path is None:
            config_path = ConfigClass.config_path
        if config_filename is None:
            config_filename = ConfigClass.config_file
        if is_cloud_mode is None:
            # Check when code is bundled using pyinstaller
            # https://pyinstaller.org/en/stable/runtime-information.html#run-time-information
            is_bundled = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
            is_cloud_mode = is_bundled and (Path(sys._MEIPASS) / 'ENABLE_CLOUD_MODE').is_file()

        config_path = Path(config_path)
        if not config_path.exists():
            config_path.mkdir(mode=0o0700, exist_ok=False)

        current_user_id = os.geteuid()

        error = self._check_user_permissions(config_path, current_user_id, (0o0500, 0o0700))
        if error and not is_cloud_mode:
            SrvErrorHandler.customized_handle(ECustomizedError.CONFIG_INVALID_PERMISSIONS, True, error)
            return

        config_file = config_path / config_filename
        if not config_file.exists():
            config_file.touch(mode=0o0600, exist_ok=False)

        error = self._check_user_permissions(config_file, current_user_id, (0o0400, 0o0600))
        if error and not is_cloud_mode:
            SrvErrorHandler.customized_handle(ECustomizedError.CONFIG_INVALID_PERMISSIONS, True, error)
            return

        self.is_cloud_mode = is_cloud_mode
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)
        if not self.config.has_section('USER'):
            self.config['USER'] = {
                'username': '',
                'password': '',
                'api_key': '',
                'access_token': '',
                'refresh_token': '',
                'secret': generate_secret(),
                'last_active': int(time.time()),
                'session_id': '',
            }
            self.save()

    def _check_user_permissions(self, path: Path, expected_uid: int, expected_bits: Iterable[int]) -> Union[str, None]:
        """Check if file or folder is owned by the user and has proper access mode."""

        path_stat = path.stat()

        path_uid = path_stat.st_uid
        if path_uid != expected_uid:
            return f'"{path}" is owned by the user id {path_uid}. Expected user id is {expected_uid}.'

        path_protection_bits = stat.S_IMODE(path_stat.st_mode)
        if path_protection_bits not in expected_bits:
            existing_permissions = oct(path_protection_bits).replace('0o', '')
            expected_permissions = ', '.join(map(oct, expected_bits)).replace('0o', '')
            return (
                f'Permissions {existing_permissions} for "{path}" are too open. '
                f'Expected permissions are {expected_permissions}.'
            )

        return None

    def save(self):
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def clear(self):
        self.config['USER'] = {
            'username': '',
            'password': '',
            'api_key': '',
            'access_token': '',
            'refresh_token': '',
            'secret': generate_secret(),
            'last_active': 0,
            'session_id': '',
        }
        self.save()

    def is_logged_in(self) -> bool:
        return bool(self.api_key or (self.access_token and self.refresh_token))

    @property
    def username(self):
        return decryption(self.config['USER']['username'], self.secret)

    @username.setter
    def username(self, val):
        self.config['USER']['username'] = encryption(val, self.secret)

    @property
    def password(self):
        return decryption(self.config['USER']['password'], self.secret)

    @password.setter
    def password(self, val):
        self.config['USER']['password'] = encryption(val, self.secret)

    @property
    def api_key(self):
        return decryption(self.config['USER']['api_key'], self.secret)

    @api_key.setter
    def api_key(self, val):
        self.config['USER']['api_key'] = encryption(val, self.secret)

    @property
    def access_token(self):
        return decryption(self.config['USER']['access_token'], self.secret)

    @access_token.setter
    def access_token(self, val):
        self.config['USER']['access_token'] = encryption(val, self.secret)

    @property
    def refresh_token(self):
        return decryption(self.config['USER']['refresh_token'], self.secret)

    @refresh_token.setter
    def refresh_token(self, val):
        self.config['USER']['refresh_token'] = encryption(val, self.secret)

    @property
    def secret(self):
        return self.config['USER']['secret']

    @secret.setter
    def secret(self, val):
        self.config['USER']['secret'] = val

    @property
    def last_active(self):
        return self.config['USER']['last_active']

    @last_active.setter
    def last_active(self, val):
        self.config['USER']['last_active'] = val

    @property
    def session_id(self):
        return self.config['USER']['session_id']

    @session_id.setter
    def session_id(self, val):
        self.config['USER']['session_id'] = val
