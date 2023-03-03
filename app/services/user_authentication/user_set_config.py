# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

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
