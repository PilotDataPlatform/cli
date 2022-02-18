from sys import version
from app.models.service_meta_class import MetaService
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from ..user_authentication.decorator import require_valid_token
import requests
from tqdm import tqdm
import click
import os
import datetime
import time
import app.services.logger_services.log_functions as logger
from app.services.output_manager.error_handler import SrvErrorHandler, ECustomizedError
from app.services.output_manager.message_handler import SrvOutPutHandler


class SrvDatasetDownloadManager(metaclass=MetaService):
    def __init__(self, output_path, dataset_code, dataset_geid):
        self.user = UserConfig()
        self.output = output_path
        self.dataset_code = dataset_code
        self.dataset_geid = dataset_geid
        self.session_id = "cli-" + str(int(time.time()))
        self.hash_code = ''
        self.version = ''
        self.download_url = ''
      
    @require_valid_token()
    def pre_dataset_version_download(self):
        url = AppConfig.Connections.url_dataset + f'/{self.dataset_geid}/download/pre'
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
            'Refresh-token': self.user.refresh_token,
            'Session-ID': self.session_id
        }
        payload = {'version': self.version}
        response = requests.get(url, headers=headers, params=payload)
        try:
            res = response.json()
            return res
        except Exception as e:
            SrvErrorHandler.default_handle(response.content, True)
    
    @require_valid_token()
    def pre_dataset_download(self):
        url = AppConfig.Connections.url_dataset_v2download + f'/download/pre'
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
            'Refresh-token': self.user.refresh_token,
            'Session-ID': self.session_id
        }
        payload = {
            "dataset_geid": self.dataset_geid,
            "session_id": self.session_id,
            "operator": self.user.username}
        response = requests.post(url, headers=headers, json=payload)
        try:
            res = response.json()
            return res
        except Exception as e:
            SrvErrorHandler.default_handle(response.content, True)

    def generate_download_url(self):
        if self.version:
            self.download_url = AppConfig.Connections.url_dataset_v2download + f"/download/{self.hash_code}"
        else:
            self.download_url = AppConfig.Connections.url_download_core + f"/download/{self.hash_code}"

    @require_valid_token()
    def download_status(self):
        url = AppConfig.Connections.url_download_core + f"/download/status/{self.hash_code}"
        res = requests.get(url)
        res_json = res.json()
        if res_json.get('code') == 200:
            status = res_json.get('result').get('status')
            return status
        else:
            SrvErrorHandler.default_handle(res_json.get('error_msg'), True)
    
    def check_download_preparing_status(self):
        while True:
            time.sleep(1)
            status = self.download_status()
            if status == 'READY_FOR_DOWNLOADING':
                break
        return status
    
    @require_valid_token()
    def send_download_request(self):
        logger.info("start downloading...")
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
        }
        with requests.get(self.download_url, headers=headers, stream=True) as r:
            r.raise_for_status()
            default_filename = str(r.headers.get('content-disposition', '')).lstrip('attachment; filename')[1:].strip('"')
            filename = f"{self.dataset_code}_{self.version}_{str(datetime.datetime.now())}" if not default_filename else default_filename
            output_path = self.avoid_duplicate_file_name(self.output.rstrip('/') + '/' + filename)
            self.total_size = int(r.headers.get('Content-length'))
            with open(output_path, 'wb') as file, tqdm(
                    desc='Downloading {}'.format(filename),
                    unit='iB',
                    unit_scale=True,
                            total=self.total_size,
                unit_divisor=1024,
                    bar_format="{desc} |{bar:30} {percentage:3.0f}% {remaining}"
            ) as bar:
                for data in r.iter_content(chunk_size=1024):
                    size = file.write(data)
                    bar.update(size)
        return output_path

    def avoid_duplicate_file_name(self, filename):
        suffix = 1
        original_filename = filename
        file, ext = os.path.splitext(original_filename)
        while True:
            if os.path.isfile(filename):
                filename = file + f' ({suffix})' + ext
                suffix  += 1
            else:
                if filename == original_filename:
                    break
                else:
                    logger.warn(f"{original_filename} already exist, file will be saved as {filename}")
                    break
        return filename

    @require_valid_token()
    def download_dataset(self):
        logger.info('Pre downloading dataset')
        pre_result = self.pre_dataset_download()
        self.hash_code = pre_result.get('result').get('payload').get('hash_code')
        self.generate_download_url()
        status = self.check_download_preparing_status()
        SrvOutPutHandler.download_status(status)
        saved_filename = self.send_download_request()
        if os.path.isfile(saved_filename):
            SrvOutPutHandler.download_success(saved_filename)
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, True)

    @require_valid_token()
    def download_dataset_version(self, version):
        logger.info('Pre downloading dataset')
        self.version = version
        pre_result = self.pre_dataset_version_download()
        self.hash_code = pre_result.get('result').get('download_hash')
        self.generate_download_url()
        saved_filename = self.send_download_request()
        if os.path.isfile(saved_filename):
            SrvOutPutHandler.download_success(saved_filename)
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, True)
