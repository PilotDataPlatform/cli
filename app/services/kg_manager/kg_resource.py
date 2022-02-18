from app.services.file_manager.file_upload import get_file_in_folder
from app.services.user_authentication.decorator import require_valid_token
from app.models.service_meta_class import MetaService
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
import collections
import requests
import json
import os
import app.services.logger_services.log_functions as logger
from app.services.output_manager.error_handler import SrvErrorHandler, ECustomizedError, OverSizeError, customized_error_msg
from app.services.output_manager.message_handler import SrvOutPutHandler
from ...utils.aggregated import get_file_in_folder



class SrvKGResourceMgr(metaclass=MetaService):
    def __init__(self, paths):
        self.user = UserConfig()
        self.paths = paths

    def pre_load_data(self, paths):
        json_data = {}
        for path in paths:
            try:
                self.validate_file_size(path)
                with open(path) as f:
                    json_data[path] = json.load(f)
            except json.decoder.JSONDecodeError:
                SrvErrorHandler.customized_handle(ECustomizedError.INVALID_ACTION, False, f"{path} is an invalid json file")
                continue
            except OverSizeError as e:
                SrvErrorHandler.default_handle(str(e), False)
                continue
            except Exception as e:
                SrvErrorHandler.customized_handle(ECustomizedError.INVALID_ACTION, False, f"{path} is an invalid json file")
                continue
        return json_data
    
    def validate_file_size(self, path):
        size = os.path.getsize(path)
        if size > 1000000:
            raise OverSizeError(customized_error_msg(ECustomizedError.OVER_SIZE) % path)

    @require_valid_token()
    def import_resource(self):
        url = AppConfig.Connections.url_bff + "/v1/kg/resources"
        file_to_process = []
        try:
            for path in self.paths:
                path = os.path.relpath(path)
                if os.path.isdir(path):
                    files = get_file_in_folder(path)
                    file_to_process = file_to_process + files
                else:
                    file_to_process.append(path)
            duplicate_file_list = [f for f, count in collections.Counter(file_to_process).items() if count > 1]
            if duplicate_file_list:
                duplicate_files = ", \n".join(duplicate_file_list)
                logger.warn(f"Following files have multiple input, it will process one time: \n{duplicate_files}")
            json_data = self.pre_load_data(file_to_process)
            if not json_data:
                return
           
            payload = {
                "dataset_code": [],
                "data": json_data
            }
            headers = {
                'Authorization': "Bearer " + self.user.access_token
            }
            res = requests.post(url, headers=headers, json=payload)
            response = res.json()
            code =response.get("code")
            result = response.get("result")
            if code == 200:
                ignored = result.get("ignored")
                processed = result.get("processing")
                if ignored:
                    ignored_files = ", \n".join(list(ignored.keys()))
                    logger.warn(f"File skipped: \n{ignored_files}")
                if processed:
                    processed_files = ", \n".join(list(processed.keys()))
                    logger.succeed(f"File imported: \n{processed_files}")
            else:
                SrvErrorHandler.customized_handle(ECustomizedError.ERROR_CONNECTION, True)
        except Exception as e:
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_ACTION, False, str(e))
