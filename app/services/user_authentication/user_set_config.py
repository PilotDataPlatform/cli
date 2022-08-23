import shutil
from app.configs import app_config
from app.services.logger_services import log_functions as logger
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.error_handler import ECustomizedError


def check_config():
    connections = app_config.AppConfig.Connections.__dict__
    for k, v in connections.items():
        if k.startswith('url') and not v:
            SrvErrorHandler.customized_handle(ECustomizedError.NO_CONFIG_FILE, True)


def set_config(target_path, destination):
    shutil.copy(target_path, destination)
    logger.succeed(f'config file set')
