# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import datetime
import os
import time
from typing import Any
from typing import Dict

import requests
from tqdm import tqdm

import app.services.logger_services.log_functions as logger
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.dataset_manager.model import EFileStatus
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.message_handler import SrvOutPutHandler
from app.utils.aggregated import resilient_session

from ..user_authentication.decorator import require_valid_token


class SrvDatasetDownloadManager(metaclass=MetaService):
    def __init__(self, output_path, dataset_code, dataset_geid):
        self.user = UserConfig()
        self.output = output_path
        self.dataset_code = dataset_code
        self.dataset_geid = dataset_geid
        self.session_id = UserConfig().session_id
        self.hash_code = ''
        self.version = ''
        self.download_url = ''
        self.default_filename = ''

    @require_valid_token()
    def pre_dataset_version_download(self):
        url = AppConfig.Connections.url_dataset + f'/{self.dataset_geid}/download/pre'
        headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
            'Refresh-token': self.user.refresh_token,
            'Session-ID': self.session_id,
        }
        payload = {'version': self.version}
        response = resilient_session().get(url, headers=headers, params=payload)
        res = response.json()
        code = response.status_code
        if code == 200:
            return res
        elif code == 404:
            SrvErrorHandler.customized_handle(ECustomizedError.VERSION_NOT_EXIST, True, self.version)
        else:
            SrvErrorHandler.default_handle(response.content, True)

    @require_valid_token()
    def pre_dataset_download(self) -> Dict[str, Any]:
        url = AppConfig.Connections.url_dataset_v2download + '/download/pre'
        headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
            'Refresh-token': self.user.refresh_token,
            'Session-ID': self.session_id,
        }
        payload = {'dataset_code': self.dataset_code, 'session_id': self.session_id, 'operator': self.user.username}
        try:
            response = resilient_session().post(url, headers=headers, json=payload)
            res = response.json()
            return res

        except Exception as e:
            SrvErrorHandler.default_handle(f'error when pre dataset download:{e}', True)

    @require_valid_token()
    def download_status(self) -> EFileStatus:
        url = AppConfig.Connections.url_download_core + f'v1/download/status/{self.hash_code}'
        res = resilient_session().get(url)
        if res.status_code == 200:
            res_json = res.json()
            status = res_json.get('result').get('status')
            return EFileStatus(status)
        else:
            SrvErrorHandler.default_handle(res_json.get('error_msg'), True)

    def check_download_preparing_status(self) -> EFileStatus:
        while True:
            time.sleep(1)
            status = self.download_status()
            if status not in [EFileStatus.RUNNING, EFileStatus.WAITING]:
                break
        return status

    @require_valid_token()
    def send_download_request(self) -> str:
        logger.info('start downloading...')

        with requests.get(self.download_url, stream=True, allow_redirects=True) as r:
            r.raise_for_status()
            # Since version zip file was created by our system, thus no need to consider filename contain '?'
            if not self.default_filename:
                filename = f'{self.dataset_code}_{self.version}_{str(datetime.datetime.now())}.zip'
            else:
                filename = self.default_filename

            output_path = self.avoid_duplicate_file_name(self.output.rstrip('/') + '/' + filename)
            self.total_size = int(r.headers.get('Content-length'))
            with open(output_path, 'wb') as file, tqdm(
                desc='Downloading {}'.format(filename),
                unit='iB',
                unit_scale=True,
                total=self.total_size,
                unit_divisor=1024,
                bar_format='{desc} |{bar:30} {percentage:3.0f}% {remaining}',
            ) as bar:
                for data in r.iter_content(chunk_size=1024):
                    size = file.write(data)
                    bar.update(size)
        return output_path

    def avoid_duplicate_file_name(self, filename) -> str:
        suffix = 1
        original_filename = filename
        file, ext = os.path.splitext(original_filename)
        while True:
            if os.path.isfile(filename):
                filename = file + f' ({suffix})' + ext
                suffix += 1
            else:
                if filename == original_filename:
                    break
                else:
                    logger.warning(f'{original_filename} already exist, file will be saved as {filename}')
                    break
        return filename

    @require_valid_token()
    def download_dataset(self) -> None:
        pre_result = self.pre_dataset_download()
        self.hash_code = pre_result.get('result').get('payload').get('hash_code')
        self.download_url = AppConfig.Connections.url_download_core + f'v1/download/{self.hash_code}'
        # format the naming for the default filename
        self.default_filename = pre_result.get('result').get('target_names')[0]
        self.default_filename = self.default_filename.split('/')[-1]

        # wait the download status to be ready
        status = self.check_download_preparing_status()
        SrvOutPutHandler.download_status(status)
        saved_filename = self.send_download_request()
        if os.path.isfile(saved_filename):
            SrvOutPutHandler.download_success(saved_filename)
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, True)

    @require_valid_token()
    def download_dataset_version(self, version) -> None:
        self.version = version
        pre_result = self.pre_dataset_version_download()
        self.download_url = pre_result.get('result').get('source')

        saved_filename = self.send_download_request()
        if os.path.isfile(saved_filename):
            SrvOutPutHandler.download_success(saved_filename)
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, True)
