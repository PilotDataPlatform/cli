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

import os
import shutil

from app.configs import app_config
from app.services.logger_services import log_functions as logger
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler


def check_config():
    connections = app_config.AppConfig.Connections.__dict__
    for k, v in connections.items():
        if k.startswith('url') and not v:
            SrvErrorHandler.customized_handle(ECustomizedError.CONFIG_NOT_FOUND, True)


def set_config(target_path, destination):
    config_path = os.path.join(destination, '.env')
    if os.path.isfile(config_path):
        SrvErrorHandler.customized_handle(ECustomizedError.CONFIG_EXIST, True)
    else:
        shutil.copy(target_path, destination)
        logger.succeed('config file set')
