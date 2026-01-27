# Copyright (C) 2022-2026 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import concurrent.futures
import os
import random
import time

import click
import httpx
import jwt
from tqdm import tqdm

import app.services.logger_services.log_functions as logger
import app.services.output_manager.message_handler as mhandler
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.item import ItemZone
from app.models.service_meta_class import MetaService
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token

from .model import EFileStatus


class SrvFileDownload(BaseAuthClient, metaclass=MetaService):
    def __init__(self, zone: str, interactive=True):
        super().__init__(AppConfig.Connections.url_fileops_greenroom)

        self.appconfig = AppConfig()
        self.user = UserConfig()
        self.operator = self.user.username
        self.session_id = UserConfig().session_id
        self.file_geid = ''
        self.hash_code = ''
        self.total_size = ''
        self.interactive = interactive
        self.check_point = False
        self.core = self.appconfig.Env.core_zone
        self.green = self.appconfig.Env.green_zone
        self.zone = zone
        self.url = {
            ItemZone.GREENROOM.value: self.appconfig.Connections.url_fileops_greenroom,
            ItemZone.CORE.value: self.appconfig.Connections.url_fileops_core,
        }.get(zone)

        self.endpoint = self.appconfig.Connections.url_fileops_greenroom + '/v1'

    def print_prepare_msg(self, message):
        space_width = len(message)
        finished_msg = message.replace('ing', 'ed')
        while True:
            if self.check_point:
                click.secho(f"{finished_msg}{' ' * space_width}\r", fg='white', nl=False)
                break
            click.secho(f"{message}{' ' * space_width}\r", fg='white', nl=False)
            for i in range(5):
                time.sleep(1)
                click.secho(f"{message}{'.' * i}\r", fg='white', nl=False)

    def get_download_url(self, zone):
        if zone == ItemZone.GREENROOM.value:
            url = self.appconfig.Connections.url_fileops_greenroom
        else:
            url = self.appconfig.Connections.url_fileops_core
        return url

    def pre_download(self):
        # with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        #     f1 = executor.submit(self.print_prepare_msg, 'preparing')
        #     f2 = executor.submit(self.prepare_download)
        #     for _ in concurrent.futures.wait([f1, f2], return_when='FIRST_COMPLETED'):
        #         pre_status, file_path = f2.result()
        # self.print_prepare_msg('preparing')
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
        try:
            self.endpoint = self.appconfig.Connections.url_bff + '/v1'
            res = self._post(f'project/{self.project_code}/files/download', json=payload)
        except httpx.HTTPStatusError as e:
            res = e.response
            if res.status_code == 403:
                SrvErrorHandler.customized_handle(ECustomizedError.NO_FILE_PERMMISION, if_exit=self.interactive)
            elif res.status_code == 400:
                SrvErrorHandler.customized_handle(ECustomizedError.FOLDER_EMPTY, if_exit=self.interactive)
            else:
                SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, if_exit=self.interactive)
        finally:
            self.endpoint = self.appconfig.Connections.url_fileops_greenroom + '/v1'

        self.check_point = True

        # fetch the info from hash token
        response = res.json().get('result')
        self.hash_code = response.get('payload', {}).get('hash_code')
        download_info = jwt.decode(self.hash_code, options={'verify_signature': False}, algorithms=['HS256'])
        file_path = download_info.get('file_path')
        pre_status = EFileStatus(response.get('status'))

        return pre_status, file_path

    @require_valid_token()
    def download_status(self):

        try:
            res = self._get(f'download/status/{self.hash_code}')
        except httpx.HTTPStatusError as e:
            res = e.response
            SrvErrorHandler.default_handle(res.content, self.interactive)

        res_json = res.json().get('result')
        status = EFileStatus(res_json.get('status'))
        return status

    def generate_download_url(self):
        download_url = self.url + f'/v1/download/{self.hash_code}'
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
        max_retries = 3
        retry_count = 0
        base_interval = 1
        max_backoff = 10

        while True:
            try:
                time.sleep(1)
                status = self.download_status()

                if status == EFileStatus.SUCCEED:
                    self.check_point = True
                    return status
                elif status == EFileStatus.FAILED:
                    self.check_point = True
                    SrvErrorHandler.customized_handle(
                        ECustomizedError.DOWNLOAD_PREPARING_FAILED, if_exit=self.interactive
                    )
                    return status

            except Exception as e:
                retry_count += 1

                if retry_count >= max_retries:
                    error_msg = f'Failed to check download status after {max_retries} attempts: {str(e)}'
                    logger.error(error_msg)

                    # IMPORTANT: Set checkpoint to true BEFORE handling the error
                    self.check_point = True

                    SrvErrorHandler.customized_handle(
                        ECustomizedError.DOWNLOAD_STATUS_CHECK_FAILED, if_exit=self.interactive
                    )
                    return EFileStatus.FAILED

                # Calculate backoff with exponential increase
                # 1st retry: ~1s, 2nd retry: ~2s, 3rd retry: ~4s, etc.
                retry_interval = min(base_interval * (2 ** (retry_count - 1)), max_backoff)

                # Add jitter (±20%) for thundering herd
                jitter = retry_interval * 0.2 * (random.random() * 2 - 1)
                retry_interval = max(0.1, retry_interval + jitter)

                logger.warning(
                    f'Error checking status (attempt {retry_count}/{max_retries}). Retrying in {retry_interval:.1f}s.'
                )

                time.sleep(retry_interval)

    def check_download_preparing_status(self):
        executor = None
        not_done = []
        try:
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
            f1 = executor.submit(self.print_prepare_msg, 'checking status')
            f2 = executor.submit(self.get_download_preparing_status)

            done, not_done = concurrent.futures.wait([f1, f2], return_when=concurrent.futures.FIRST_COMPLETED)

            # If status thread finished first, get its result
            if f2 in done:
                status = f2.result()
                self.check_point = True
                return status
            else:
                # If message thread somehow finished first (shouldn't normally happen)
                # Wait for status thread with a timeout
                try:
                    status = f2.result(timeout=10)  # 10 second timeout
                    self.check_point = True
                    return status
                except concurrent.futures.TimeoutError:
                    self.check_point = True
                    logger.error('Status check timed out')
                    SrvErrorHandler.customized_handle(
                        ECustomizedError.DOWNLOAD_STATUS_CHECK_FAILED, if_exit=self.interactive
                    )
                    return EFileStatus.FAILED

        except Exception as e:
            self.check_point = True

            logger.error(f'Error in download status check: {str(e)}')
            SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_STATUS_CHECK_FAILED, if_exit=self.interactive)
            return EFileStatus.FAILED
        finally:
            if executor:
                # Cancel any pending futures and shut down the executor
                for future in not_done:
                    future.cancel()
                executor.shutdown(wait=False)

    @require_valid_token()
    def download_file(self, url, local_filename, download_mode='single'):  # noqa: C901
        logger.info('start downloading...')
        filename = local_filename.split('/')[-1]
        max_retries = 3
        retry_count = 0
        # Retry logic for handling read timeouts
        while retry_count <= max_retries:
            try:
                with httpx.stream('GET', url, timeout=httpx.Timeout(30.0, read=300.0)) as r:
                    r.raise_for_status()

                    if r.headers.get('Content-Type') == 'application/zip' or download_mode == 'batch':
                        size = r.headers.get('Content-length')
                        self.total_size = int(size) if size else self.total_size

                    stream_iter = r.iter_bytes(chunk_size=1024)
                    if self.total_size:
                        downloaded_size = 0
                        with open(local_filename, 'wb') as file, tqdm(
                            desc=f'Downloading {filename}',
                            total=self.total_size,
                            unit='iB',
                            unit_scale=True,
                            unit_divisor=1024,
                            bar_format='{desc} |{bar:30} {percentage:3.0f}% {remaining}',
                        ) as bar:
                            try:
                                for data in stream_iter:
                                    size = file.write(data)
                                    bar.update(size)
                                    downloaded_size += len(data)
                            except httpx.ReadTimeout:
                                # Re-raise so it's caught by the outer exception handler
                                raise

                        if downloaded_size != self.total_size:
                            SrvErrorHandler.customized_handle(
                                ECustomizedError.DOWNLOAD_SIZE_MISMATCH,
                                if_exit=self.interactive,
                                value=(self.total_size, downloaded_size),
                            )
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

                return local_filename

            except httpx.ReadTimeout:
                retry_count += 1
                if retry_count > max_retries:
                    logger.error(f'Download failed after {max_retries} attempts due to read timeout')
                    SrvErrorHandler.customized_handle(
                        ECustomizedError.DOWNLOAD_TIMEOUT, if_exit=self.interactive, value=filename
                    )
                    return None
                wait_time = 2**retry_count
                logger.warning(f'Read timeout encountered, retrying in {wait_time}s ({retry_count}/{max_retries})')
                time.sleep(wait_time)

            except Exception as e:
                logger.error(f'Error downloading: {e}')
                return None

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
                self.endpoint = self.get_download_url(self.zone)
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
