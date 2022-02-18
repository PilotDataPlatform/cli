import time
from tqdm import tqdm
import os
import click
import concurrent.futures
from app.configs.app_config import AppConfig
import app.services.logger_services.log_functions as logger
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler
import requests
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import get_source_file, get_user_info, get_folder_in_project
import app.services.output_manager.message_handler as mhandler
import app.services.output_manager.error_handler as ehandler
from app.utils.aggregated import void_validate_zone, get_zone


class SrvFileDownload(metaclass=MetaService):

    def __init__(self, path, zone, project_code, project_geid, by_geid=False, interactive=True):
        self.appconfig =  AppConfig()
        self.user = UserConfig()
        self.user_info = get_user_info()
        self.operator = self.user_info['preferred_username']
        self.session_id = "cli-" + str(int(time.time()))
        self.path = path if isinstance(path, list) else [path]
        self.zone = get_zone(zone)
        self.project_geid = project_geid
        self.project_code = project_code
        self.file_geid = ''
        self.hash_code = ''
        self.total_size = ''
        self.by_geid = by_geid
        self.interactive=interactive
        self.url = ""
        self.check_point = False
        self.core = self.appconfig.Env.core_zone
        self.green = self.appconfig.Env.green_zone
    
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
        void_validate_zone('download', zone, self.user.access_token)
        if zone == 'greenroom':
            url = self.appconfig.Connections.url_download_greenroom
        else:
            url = self.appconfig.Connections.url_download_core
        return url

    def pre_download(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(self.print_prepare_msg, 'preparing')
            f2 = executor.submit(self.prepare_download)
            for f in concurrent.futures.wait([f1, f2], return_when='FIRST_COMPLETED'):
                pre_status, file_path = f2.result()
        self.check_point = False
        return pre_status, file_path

    @require_valid_token()
    def prepare_download(self):
        url = self.appconfig.Connections.url_v2_download_pre
        files = []
        for f in self.file_geid:
            files.append({'geid': f})
        payload = {'files': files,
                   'operator': self.operator,
                   'project_code': self.project_code,
                   'session_id': self.session_id,
                   'zone': self.zone}
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
            'Refresh-token': self.user.refresh_token,
            'Session-ID': self.session_id
        }
        res = requests.post(url, headers=headers, json=payload)
        res_json = res.json()
        self.check_point = True
        if res_json.get('code') == 200:
            file_path = res_json.get('result').get('source')
            pre_status = res_json.get('result').get('status')
        elif res_json.get('code') == 403:
            ehandler.SrvErrorHandler.customized_handle(ECustomizedError.NO_FILE_PERMMISION, self.interactive)
        elif res_json.get('code') == 400 and res_json.get('error_msg') == 'Folder is empty':
            ehandler.SrvErrorHandler.customized_handle(ECustomizedError.FOLDER_EMPTY, self.interactive)
        else:
            ehandler.SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, self.interactive)
        result = res_json.get('result')
        h_code = result.get('payload').get('hash_code')
        self.hash_code = h_code
        return pre_status, file_path

    @require_valid_token()
    def download_status(self):
        url = self.url + f"/download/status/{self.hash_code}"
        res = requests.get(url)
        res_json = res.json()
        if res_json.get('code') == 200:
            status = res_json.get('result').get('status')
            return status
        else:
            ehandler.SrvErrorHandler.default_handle(res_json.get('error_msg'), self.interactive)

    def generate_download_url(self):
        download_url = self.url + f"/download/{self.hash_code}"
        return download_url

    @require_valid_token()
    def validate_file_status(self):
        payload = {"operation": "download",
                   "project_geid": self.project_geid,
                   "operator": self.operator,
                   "payload": {
                       "targets": [{'geid': self.file_geid}]}
                   }
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
            'Session-ID': self.session_id
        }
        url = self.appconfig.Connections.url_validation
        res = requests.post(url, headers=headers, json=payload)
        res_json = res.json()
        if res_json.get('code') == 200 and res_json.get('result'):
            file_validation = []
            for v in res_json.get('result'):
                file_validation.append(v.get('is_valid'))
            if len(file_validation) == 1:
                valid = file_validation[0]
            elif len(set(file_validation)) > 1:
                valid = False
            else:
                valid = file_validation[0]
            valid = res_json.get('result')[0].get('is_valid')
        elif res_json.get('code') != 200:
            valid = False
        else:
            ehandler.SrvErrorHandler.customized_handle(ECustomizedError.FOLDER_EMPTY, self.interactive)
        return valid

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

    def get_download_preparing_status(self):
        while True:
            time.sleep(1)
            status = self.download_status()
            if status == 'READY_FOR_DOWNLOADING':
                self.check_point = True
                break
        return status 
    
    def check_download_preparing_status(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(self.print_prepare_msg, 'checking status')
            f2 = executor.submit(self.get_download_preparing_status)
            for f in concurrent.futures.wait([f1, f2], return_when='FIRST_COMPLETED'):
                status = f2.result()
        return status

    @require_valid_token()
    def download_file(self, url, local_filename, download_mode='single'):
        logger.info("start downloading...")
        filename = local_filename.split('/')[-1]
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            if r.headers.get('Content-Type') == 'application/zip' or download_mode == 'batch':
                size = r.headers.get('Content-length')
                self.total_size = int(size) if size else self.total_size
            if self.total_size:
                with open(local_filename, 'wb') as file, tqdm(
                        desc='Downloading {}'.format(filename),
                        total=self.total_size,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                        bar_format="{desc} |{bar:30} {percentage:3.0f}% {remaining}"
                ) as bar:
                    for data in r.iter_content(chunk_size=1024):
                        size = file.write(data)
                        bar.update(size)
                        
            else:
                with open(local_filename, 'wb') as file:
                    part = 0
                    for data in r.iter_content(chunk_size=1024):
                        size = file.write(data)
                        progress = '.' * part
                        click.echo(f"Downloading{progress}\r", nl=False)
                        if part > 5:
                            part = 0
                        else:
                            part += 1
                    logger.info('Download complete')
        return local_filename

    @require_valid_token()
    def group_file_geid_by_project(self):
        payload = {'geid': self.path}
        headers = {
            'Authorization': "Bearer " + self.user.access_token
        }
        url = self.appconfig.Connections.url_bff + f'/v1/query/geid'
        download_tasks = {}
        proccessed_project = []
        try:
            res = requests.post(url, headers=headers, json=payload)
            res_json = res.json()
            if res_json.get('code') == 200:
                result = res_json.get('result')
                for node in result:
                    node_info = node.get('result')
                    file_geid = node.get('geid')
                    if node.get('status') == 'success':
                        neo_labels = node_info[0].get('labels') if node_info else []
                        labels = [x.lower() for x in neo_labels]
                        total_size = node_info[0].get('file_size')
                        project_code = node_info[0].get('project_code')
                        if project_code + f'_{self.core}' in proccessed_project and self.core in labels:
                            download_tasks[project_code + f'_{self.core}']['files'] = download_tasks.get(f'{project_code}_{self.core}', {}).get('files') + [file_geid]
                        elif project_code + f'_{self.green}' in proccessed_project and self.green in labels:
                            download_tasks[project_code + f'_{self.green}']['files'] = download_tasks.get(f'{project_code}_{self.green}', {}).get('files') + [file_geid]
                        else:
                            current_label = self.green if self.green in labels else self.core
                            proccessed_project.append(f'{project_code}_{current_label}')
                            download_tasks[f'{project_code}_{current_label}'] = {'files': download_tasks.get(f'{project_code}_{current_label}', []) + [file_geid], 'total_size': total_size}
                    elif node.get('status') == 'Permission Denied':
                        ehandler.SrvErrorHandler.customized_handle(ECustomizedError.NO_FILE_PERMMISION, self.interactive)
                    elif node.get('status') == 'File Not Exist':
                        ehandler.SrvErrorHandler.customized_handle(ECustomizedError.INVALID_DOWNLOAD, self.interactive, value=file_geid)
                    elif node.get('status') == 'Can only work on file or folder not in Trash Bin':
                        ehandler.SrvErrorHandler.customized_handle(ECustomizedError.INVALID_DOWNLOAD, self.interactive, value="Can only download file or folder")
                    else:
                        ehandler.SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, self.interactive)
                return download_tasks
            else:
                ehandler.SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, self.interactive)
        except Exception as e:
            ehandler.SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, self.interactive)

    @require_valid_token()
    def group_file_path_by_project(self):
        download_tasks = {}
        proccessed_project = []
        for p in self.path:
            project_path = p.strip('/').split('/')
            project_code = project_path[0]
            file_rel_path = '/'.join(project_path[1:])
            check_if_folder = '/'.join(p.split('/')[1:])
            filename = p.split('/')[-1]
            folder_dir = check_if_folder.split('/')
            for i in range(len(folder_dir)-1):
                transiant_path = '/'.join(folder_dir[0:i+1]).rstrip('/')
                _transiant_permission = get_folder_in_project(self.project_code, self.zone, transiant_path, self.user.access_token)
            check_res = get_folder_in_project(project_code, self.zone, check_if_folder, self.user.access_token)
            if check_res:
                file_geid = check_res.get('global_entity_id')
                total_size = ''
            else:
                file_info = get_source_file(file_rel_path,
                                            project_code,
                                            self.user.access_token,
                                            namespace=self.zone,
                                            interactive=self.interactive)
                if not file_info:
                    ehandler.SrvErrorHandler.customized_handle(ECustomizedError.INVALID_DOWNLOAD,
                    False, value=p)
                    continue
                file_geid = file_info[0].get('global_entity_id')
                total_size = file_info[0].get('file_size')
            # Add file to core files list 
            if project_code + f'_{self.core}' in proccessed_project and self.core == self.zone:
                download_tasks[project_code + f'_{self.core}']['files'] = download_tasks.get(f'{project_code}_{self.core}', {}).get('files') + [file_geid]
            # Add file to greenroom files list
            elif project_code + f'_{self.green}' in proccessed_project and self.green == self.zone.lower():
                download_tasks[project_code + '_greenroom']['files'] = download_tasks.get(f'{project_code}_greenroom', {}).get('files') + [file_geid]
            # Add file to list and denote as greenroom/core list
            else:
                current_label = self.green if self.green == self.zone else self.core
                proccessed_project.append(f'{project_code}_{current_label}')
                download_tasks[f'{project_code}_{current_label}'] = {'files': download_tasks.get(f'{project_code}_{current_label}', []) + [file_geid], 'total_size': total_size}
        # download task: {project_code_zone: files['geid1', 'geid2'], 'total_size': '1M'}
        for k, v in download_tasks.items():
            total_files = download_tasks.get(k).get('files')
            # if more than 1 file in the list, take file size from response header and remove current size
            if len(total_files) > 1:
                download_tasks[k]['total_size'] = 0
        return download_tasks

    @require_valid_token()
    def simple_download_file(self, output_path):
        click.secho("preparing\r", fg='white', nl=False)
        if self.by_geid:
            download_tasks = self.group_file_geid_by_project()
            if not download_tasks:
                return False
            for k, v in download_tasks.items():
                self.project_code = k.split('_')[0]
                self.zone = k.split('_')[1]
                self.file_geid = v.get('files')
                self.total_size = v.get('total_size')
                self.url = self.get_download_url(self.zone)
        else:
            self.path = self.path[0]
            project_path = self.path.strip('/').split('/')
            project_code = project_path[0]
            file_rel_path = '/'.join(project_path[1:])
            check_if_folder = '/'.join(self.path.split('/')[1:])
            filename = self.path.split('/')[-1]
            folder_dir = check_if_folder.split('/')
            self.url = self.get_download_url(self.zone)
            for i in range(len(folder_dir)-1):
                transiant_path = '/'.join(folder_dir[0:i+1]).rstrip('/')
                transiant_permission = get_folder_in_project(self.project_code, self.zone, transiant_path, self.user.access_token)
            check_res = get_folder_in_project(self.project_code, self.zone, check_if_folder, self.user.access_token)
            if check_res:
                self.file_geid = [check_res.get('global_entity_id')]
                self.total_size = ''
            else:
                file_info = get_source_file(file_rel_path,
                                            self.project_code,
                                            self.user.access_token,
                                            namespace=self.zone,
                                            interactive=self.interactive)
                if not file_info:
                    logger.warn('no file info')
                    ehandler.SrvErrorHandler.customized_handle(ECustomizedError.INVALID_DOWNLOAD, self.interactive, value=self.path)
                    return False
                self.file_geid = [file_info[0].get('global_entity_id')]
                self.total_size = file_info[0].get('file_size')
        pre_status, zip_file_path = self.pre_download()
        if pre_status =='ZIPPING':
            filename = zip_file_path.split('/')[-1]
        status = self.check_download_preparing_status()
        mhandler.SrvOutPutHandler.download_status(status)
        download_url = self.generate_download_url()
        output_filename = output_path.rstrip('/') + '/' + filename
        local_filename = self.avoid_duplicate_file_name(output_filename)
        saved_filename = self.download_file(download_url, local_filename)
        if os.path.isfile(saved_filename):
            mhandler.SrvOutPutHandler.download_success(saved_filename)
        else:
            ehandler.SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, self.interactive)

    @require_valid_token()
    def batch_download_file(self, output_path):
        logger.info('Preparing downloading')
        if self.by_geid:
            download_tasks = self.group_file_geid_by_project()
        else:
            download_tasks = self.group_file_path_by_project()
        for k, v in download_tasks.items():
            self.project_code = k.split('_')[0]
            self.zone = k.split('_')[1]
            self.file_geid = v.get('files')
            self.total_size = v.get('total_size')
            self.url = self.get_download_url(self.zone)
            pre_status, zip_file_path = self.pre_download()
            if pre_status =='ZIPPING':
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
                ehandler.SrvErrorHandler.customized_handle(ECustomizedError.DOWNLOAD_FAIL, self.interactive)
