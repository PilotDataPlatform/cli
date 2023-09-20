# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import configparser
import os
import time
from pathlib import Path

from app.models.singleton import Singleton
from app.services.crypto.crypto import decryption
from app.services.crypto.crypto import encryption
from app.services.crypto.crypto import generate_secret

from .app_config import AppConfig


class UserConfig(metaclass=Singleton):
    """The class to maintain the user access/fresh token Note here: the base class is Singleton, meaning no matter how
    code initializes the class.

    This user config is global.
    """

    def __init__(self):
        if not os.path.exists(AppConfig.Env.user_config_path):
            os.makedirs(AppConfig.Env.user_config_path)
        if not os.path.exists(AppConfig.Env.user_config_file):
            Path.touch(Path(AppConfig.Env.user_config_file))
        self.config = configparser.ConfigParser()
        self.config.read(AppConfig.Env.user_config_file)
        if not self.config.has_section('USER'):
            self.config['USER'] = {
                'username': '',
                'password': '',
                'access_token': '',
                'refresh_token': '',
                'secret': generate_secret(),
                'last_active': int(time.time()),
                'session_id': '',
            }
            self.save()

    def save(self):
        with open(AppConfig.Env.user_config_file, 'w') as configfile:
            self.config.write(configfile)

    def clear(self):
        self.config['USER'] = {
            'username': '',
            'password': '',
            'access_token': '',
            'refresh_token': '',
            'secret': generate_secret(),
            'last_active': 0,
            'session_id': '',
        }
        self.save()

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
