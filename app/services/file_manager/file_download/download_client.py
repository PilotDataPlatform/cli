# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import concurrent.futures
import os
import time

import click
import httpx
import jwt
from tqdm import tqdm

import app.services.logger_services.log_functions as logger
import app.services.output_manager.message_handler as mhandler
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import resilient_session

from .model import EFileStatus


class SrvFileDownload(metaclass=MetaService):
    def __init__(self, zone: str, interactive=True):
        self.appconfig = AppConfig()
        self.user = UserConfig()
        self.operator = self.user.username
        self.session_id = UserConfig().session_id
        self.file_geid = ''
        self.hash_code = ''
        self.total_size = ''
        self.interactive = interactive
        self.url = ''
        self.check_point = False
        self.core = self.appconfig.Env.core_zone
        self.green = self.appconfig.Env.green_zone
        self.zone = zone

    def print_prepare_msg(self, message):
        space_width = len(message)
        finished_msg = message.replace('ing', 'ed')
        while True:
            if self.check_point:
                click.secho(f"{finished_msg}{' '*space_width}\r", fg='white', nl=False)
                break
            click.secho(f"{message}{' '*space_width}\r", fg='white', nl=False)
            for i in range(5):
                time.sleep(1)
                click.secho(f"{message}{'.'*i}\r", fg='white', nl=False)

    def get_download_url(self, zone):
        if zone == 'greenroom':
            url = self.appconfig.Connections.url_download_greenroom
        else:
            url = self.appconfig.Connections.url_download_core
        return url

    def pre_download(self):
        pre_status, file_path = self.prepare_download()

        self.check_point = False
        return pre_status, file_path

    @require_valid_token()
    def prepare_download(self):
        files = []
        for f in self.file_geid:
            files.append({'id': f})
        payload = {
            'files': files,
            'zone': self.zone,
            'operator': self.operator,
            'container_code': self.project_code,
            'container_type': 'project',
        }
        headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
            'Refresh-token': self.user.refresh_token,
            'Session-ID': self.session_id,
        }
        url = self.appconfig.Connections.url_v2_download_pre % (self.project_code)
        res = resilient_session().post(url, headers=headers, json=payload)
        res_json = res.json().get('result')
        self.check_point = True

        if res.status_code == 200:
            self.hash_code = res_json.get('payload', {}).get('hash_code')
            download_info = jwt.decode(self.hash_code, options={'verify_signature': False})
            file_path = download_info.get('file_path')
            pre_status = EFileStatus(res_json.get('status'))
        elif res.status_code == 403:
            SrvErrorHandler.customized_handle(ECustomizedError.NO_FILE_PERMMISION, self.interactive)
        elif res.status_code == 400 and res_json.get('error_msg') == 'Folder is empty':
            SrvErrorHandler.customized_handle(ECustomizedError.FOLDER_EMPTY, self.interactive)
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, self.interactive)

        return pre_status, file_path

    @require_valid_token()
    def download_status(self):
        url = self.url + f'v1/download/status/{self.hash_code}'
        res = resilient_session().get(url)
        res_json = res.json().get('result')
        if res.status_code == 200:
            status = EFileStatus(res_json.get('status'))
            return status
        else:
            SrvErrorHandler.default_handle(res_json.get('error_msg'), self.interactive)

    def generate_download_url(self):
        download_url = self.url + f'v1/download/{self.hash_code}'
        return download_url

    def avoid_duplicate_file_name(self, filename):
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

    def get_download_preparing_status(self):
        while True:
            time.sleep(1)
            status = self.download_status()
            if status == EFileStatus.SUCCEED:
                self.check_point = True
                break
            elif status == EFileStatus.FAILED:
                self.check_point = True
                SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, self.interactive)
        return status

    def check_download_preparing_status(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(self.print_prepare_msg, 'checking status')
            f2 = executor.submit(self.get_download_preparing_status)
            for _ in concurrent.futures.wait([f1, f2], return_when='FIRST_COMPLETED'):
                status = f2.result()
        return status

    @require_valid_token()
    def download_file(self, url, local_filename, download_mode='single'):
        logger.info('start downloading...')
        filename = local_filename.split('/')[-1]
        try:
            with httpx.stream('GET', url) as r:
                r.raise_for_status()
                if r.headers.get('Content-Type') == 'application/zip' or download_mode == 'batch':
                    size = r.headers.get('Content-length')
                    self.total_size = int(size) if size else self.total_size
                if self.total_size:
                    with open(local_filename, 'wb') as file, tqdm(
                        desc=f'Downloading {filename}',
                        total=self.total_size,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                        bar_format='{desc} |{bar:30} {percentage:3.0f}% {remaining}',
                    ) as bar:
                        for data in r.iter_bytes(chunk_size=1024):
                            size = file.write(data)
                            bar.update(size)
                else:
                    with open(local_filename, 'wb') as file:
                        part = 0
                        for data in r.iter_bytes(chunk_size=1024):
                            size = file.write(data)
                            progress = '.' * part
                            click.echo(f'Downloading{progress}\r', nl=False)
                            if part > 5:
                                part = 0
                            else:
                                part += 1
                        logger.info('Download complete')
        except Exception as e:
            logger.error(f'Error downloading: {e}')
        return local_filename

    @require_valid_token()
    def group_file_geid_by_project(self, file_info):
        # download task: {'project_code_zone': {'files': ['ac64d430-cf25-44b6-8b49-bfb3cf624553'], 'total_size': 13958}}
        download_tasks = {}
        proccessed_project = []
        for node in file_info:
            node_info = node.get('result')
            file_geid = node.get('geid')
            if node.get('status') == 'success':
                label = self.core if node_info.get('zone') == 1 else self.green
                total_size = node_info.get('size')
                project_code = node_info.get('container_code')
                download_tasks['possible_file_name'] = node_info.get('name')
                download_tasks['download_type'] = node_info.get('type')
                # if project file/folder in the list under same zone, append accordingly to the list
                if project_code + f'_{self.core}' in proccessed_project and self.core == label:
                    download_tasks[project_code + f'_{self.core}']['files'] = download_tasks.get(
                        f'{project_code}_{self.core}', {}
                    ).get('files') + [file_geid]
                elif project_code + f'_{self.green}' in proccessed_project and self.green == label:
                    download_tasks[project_code + f'_{self.green}']['files'] = download_tasks.get(
                        f'{project_code}_{self.green}', {}
                    ).get('files') + [file_geid]
                else:
                    # If project file/folder not in the list, append to the list
                    proccessed_project.append(f'{project_code}_{label}')
                    download_tasks[f'{project_code}_{label}'] = {
                        'files': download_tasks.get(f'{project_code}_{label}', []) + [file_geid],
                        'total_size': total_size,
                    }
            elif node.get('status') == 'Permission Denied':
                SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, self.interactive)
            elif node.get('status').lower() == 'file not exist':
                SrvErrorHandler.customized_handle(ECustomizedError.INVALID_DOWNLOAD, self.interactive, value=file_geid)
            elif node.get('status') == 'Can only work on file or folder not in Trash Bin':
                SrvErrorHandler.customized_handle(
                    ECustomizedError.INVALID_DOWNLOAD, self.interactive, value='Can only download file or folder'
                )
            else:
                SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, self.interactive)
        return download_tasks

    def handle_geid_downloading(self, item_res):
        download_tasks = self.group_file_geid_by_project(item_res)
        if not download_tasks:
            return False, ''
        else:
            item_type = download_tasks.get('download_type')
            item_name = download_tasks.get('possible_file_name')
            presigned_task = True if item_type == 'file' else False
            download_tasks.pop('download_type')
            download_tasks.pop('possible_file_name')
            for k, v in download_tasks.items():
                self.project_code = k.split('_')[0]
                self.zone = k.split('_')[1]
                self.file_geid = v.get('files')
                self.total_size = v.get('total_size')
                self.url = self.get_download_url(self.zone)
        return presigned_task, item_name

    @require_valid_token()
    def simple_download_file(self, output_path, item_res):
        click.secho('preparing\r', fg='white', nl=False)
        presigned_task, filename = self.handle_geid_downloading(item_res)
        if not filename:
            return

        # genereate download url for presigned or zip download
        pre_status, zip_file_path = self.pre_download()
        if pre_status == EFileStatus.WAITING and not presigned_task:
            filename = zip_file_path.split('/')[-1]
        if presigned_task:
            download_url = zip_file_path
        else:
            status = self.check_download_preparing_status()
            mhandler.SrvOutPutHandler.download_status(status)
            download_url = self.generate_download_url()

        output_filename = output_path.rstrip('/') + '/' + filename
        local_filename = self.avoid_duplicate_file_name(output_filename)
        saved_filename = self.download_file(download_url, local_filename)

        if os.path.isfile(saved_filename):
            mhandler.SrvOutPutHandler.download_success(saved_filename)
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, self.interactive)

    @require_valid_token()
    def batch_download_file(self, output_path, item_res):
        file_to_process = [item for item in item_res if item.get('status') == 'success']
        if len(file_to_process) == 1:
            self.simple_download_file(output_path, item_res)
        else:
            _, filename = self.handle_geid_downloading(item_res)
            if not filename:
                return
            pre_status, zip_file_path = self.pre_download()
            if pre_status == EFileStatus.WAITING:
                filename = zip_file_path.split('/')[-1]
            status = self.check_download_preparing_status()
            mhandler.SrvOutPutHandler.download_status(status)
            download_url = self.generate_download_url()
            output_filename = output_path.rstrip('/') + '/' + filename
            local_filename = self.avoid_duplicate_file_name(output_filename)
            saved_filename = self.download_file(download_url, local_filename, download_mode='batch')
            if os.path.isfile(saved_filename):
                mhandler.SrvOutPutHandler.download_success(saved_filename)
            else:
                SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, self.interactive)
