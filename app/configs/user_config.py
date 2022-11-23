# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import configparser
import os
import time

from app.models.singleton import Singleton
from app.services.crypto.crypto import decryption, encryption, generate_secret

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
            os.system(r'touch {}'.format(AppConfig.Env.user_config_file))
        self.config = configparser.ConfigParser()
        self.config.read(AppConfig.Env.user_config_file)
        if not self.config.has_section('USER'):
            self.config['USER'] = {
                'username': '',
                'password': '',
                'access_token': '',
                'refresh_token': '',
                'secret': generate_secret(),
                'hpc_token': '',
                'last_active': int(time.time()),
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
            'hpc_token': '',
            'secret': generate_secret(),
            'last_active': 0,
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
    def hpc_token(self):
        return decryption(self.config['USER']['hpc_token'], self.secret)

    @hpc_token.setter
    def hpc_token(self, val):
        self.config['USER']['hpc_token'] = encryption(val, self.secret)

    @property
    def last_active(self):
        return self.config['USER']['last_active']

    @last_active.setter
    def last_active(self, val):
        self.config['USER']['last_active'] = val
