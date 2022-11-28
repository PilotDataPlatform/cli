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

import math
import os
import time
import zipfile
from multiprocessing.pool import ThreadPool

import click

# import httpx
import requests
from tqdm import tqdm

import app.models.upload_form as uf
import app.services.logger_services.log_functions as logger
import app.services.output_manager.message_handler as mhandler
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.file_manager.file_manifests import SrvFileManifests
from app.services.file_manager.file_tag import SrvFileTag
from app.services.output_manager.error_handler import (
    ECustomizedError,
    SrvErrorHandler,
    customized_error_msg,
)
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import resilient_session, search_item

from .file_lineage import create_lineage
from ...utils.aggregated import get_file_in_folder


class UploadEventValidator:
    def __init__(self, project_code, zone, upload_message, source, process_pipeline, token, attribute, tag):
        self.project_code = project_code
        self.zone = zone
        self.upload_message = upload_message
        self.source = source
        self.process_pipeline = process_pipeline
        self.token = token
        self.attribute = attribute
        self.tag = tag

    def validate_zone(self):
        source_file_info = {}
        if not self.upload_message:
            SrvErrorHandler.customized_handle(
                ECustomizedError.INVALID_UPLOAD_REQUEST, True, value='upload-message is required'
            )
        if self.source:
            if not self.process_pipeline:
                SrvErrorHandler.customized_handle(
                    ECustomizedError.INVALID_UPLOAD_REQUEST, True, value='process pipeline name required'
                )
            else:
                source_file_info = search_item(self.project_code, self.zone, self.source, 'file', self.token)
                source_file_info = source_file_info['result']
                if not source_file_info:
                    SrvErrorHandler.customized_handle(ECustomizedError.INVALID_SOURCE_FILE, True, value=self.source)
        return source_file_info

    def validate_attribute(self):
        srv_manifest = SrvFileManifests()
        if not os.path.isfile(self.attribute):
            raise Exception('Attribute not exist in the given path')
        try:
            attribute = srv_manifest.read_manifest_template(self.attribute)
            attribute = srv_manifest.convert_import(attribute, self.project_code)
            srv_manifest.validate_manifest(attribute)
            return attribute
        except Exception:
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TEMPLATE, True)

    def validate_tag(self):
        srv_tag = SrvFileTag()
        srv_tag.validate_taglist(self.tag)

    def validate_upload_event(self):
        source_file_info, loaded_attribute = {}, {}
        if self.attribute:
            loaded_attribute = self.validate_attribute()
        if self.tag:
            self.validate_tag()
        if self.zone == AppConfig.Env.core_zone.lower():
            source_file_info = self.validate_zone()
        converted_content = {'source_file': source_file_info, 'attribute': loaded_attribute}
        return converted_content


class SrvSingleFileUploader(metaclass=MetaService):
    def __init__(
        self,
        file_path,
        project_code,
        tags,
        relative_path,
        zone=AppConfig.Env.green_zone,
        upload_message='cli straight upload',
        job_type='AS_FILE',
        process_pipeline=None,
        current_folder_node='',
        regular_file=True,
    ):
        self.user = UserConfig()
        self.operator = self.user.username
        self.path = file_path
        self.upload_message = upload_message
        self.chunk_size = 1024 * 1024 * AppConfig.Env.chunk_size
        self.base_url = {
            AppConfig.Env.green_zone: AppConfig.Connections.url_upload_greenroom,
            AppConfig.Env.core_zone: AppConfig.Connections.url_upload_core,
        }.get(zone.lower())
        self.zone = zone
        self.job_type = job_type
        self.project_code = project_code
        self.process_pipeline = process_pipeline
        self.session_id = 'cli-' + str(int(time.time()))
        self.upload_form = uf.FileUploadForm()
        self.upload_form.tags = tags
        self.upload_form.uploader = self.user.username
        self.upload_form.resumable_filename = [os.path.basename(self.path[0])] if job_type == 'AS_FILE' else self.path
        self.upload_form.resumable_relative_path = relative_path
        self.current_folder_node = current_folder_node
        self.regular_file = regular_file

    def generate_meta(self):
        file_length_in_bytes = os.path.getsize(self.path)
        self.upload_form.resumable_total_size = file_length_in_bytes
        self.upload_form.resumable_total_chunks = math.ceil(self.upload_form.resumable_total_size / self.chunk_size)
        # mhandler.SrvOutPutHandler.uploading_files(
        #     self.upload_form.uploader,
        #     self.project_code,
        #     self.upload_form.resumable_total_size,
        #     self.upload_form.resumable_total_chunks,
        #     self.upload_form.resumable_relative_path.strip('/'),
        # )
        return self.upload_form.to_dict

    @require_valid_token()
    def pre_upload(self):
        url = AppConfig.Connections.url_bff + '/v1/project/{}/files'.format(self.project_code)
        payload = uf.generate_pre_upload_form(
            self.project_code,
            self.operator,
            self.upload_form,
            zone=self.zone,
            upload_message=self.upload_message,
            job_type=self.job_type,
            current_folder_node=self.current_folder_node,
        )
        headers = {'Authorization': 'Bearer ' + self.user.access_token, 'Session-ID': self.session_id}
        response = resilient_session().post(url, json=payload, headers=headers, timeout=None)

        if response.status_code == 200:
            res_to_dict = response.json()
            result = res_to_dict.get('result')
            res = {}
            for job in result:
                relative_path = job.get('source')
                resumable_id = job.get('payload').get('resumable_identifier')
                res[relative_path] = resumable_id
            mhandler.SrvOutPutHandler.preupload_success()
            return res
        elif response.status_code == 403:
            res_to_dict = response.json()
            SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, self.regular_file)
        elif response.status_code == 401:
            SrvErrorHandler.customized_handle(ECustomizedError.PROJECT_DENIED, self.regular_file)
        elif response.status_code == 409:
            SrvErrorHandler.customized_handle(ECustomizedError.FILE_EXIST, self.regular_file)
            raise Exception('file exist')
        elif response.status_code == 400 and 'Invalid operation, locked' in response.json().get('error_msg'):
            SrvErrorHandler.customized_handle(ECustomizedError.FILE_LOCKED, True)
        elif response.status_code == 500 and 'Invalid operation, locked' in response.json().get('error_msg'):
            SrvErrorHandler.customized_handle(ECustomizedError.FILE_LOCKED, True)
        else:
            SrvErrorHandler.default_handle(str(response.status_code) + ': ' + str(response.content), self.regular_file)

    def stream_upload(self):
        count = 0
        remaining_size = self.upload_form.resumable_total_size
        with tqdm(
            total=self.upload_form.resumable_total_size,
            leave=True,
            bar_format='{desc} |{bar:30} {percentage:3.0f}% {remaining}',
        ) as bar:
            bar.set_description('Uploading {}'.format(self.upload_form.resumable_filename))
            f = open(self.path, 'rb')
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                else:
                    self.upload_chunk(count + 1, chunk)
                    if self.chunk_size > remaining_size:
                        bar.update(remaining_size)
                    else:
                        bar.update(self.chunk_size)
                    count += 1  # uploaded successfully
                    remaining_size = remaining_size - self.chunk_size
            f.close()

    @require_valid_token()
    def upload_chunk(self, chunk_number, chunk):
        # retry three times
        for i in range(AppConfig.Env.resilient_retry):
            if i > 0:
                SrvErrorHandler.default_handle('retry number %s' % i)
            url = self.base_url + '/v1/files/chunks'
            payload = uf.generate_chunk_form(self.project_code, self.operator, self.upload_form, chunk_number)
            headers = {'Authorization': 'Bearer ' + self.user.access_token, 'Session-ID': self.session_id}
            # print(self.user.access_token)
            files = {'chunk_data': chunk}
            # start_time = time.time()
            response = requests.post(url, data=payload, headers=headers, files=files)
            # print(f'\napi {url} spent {time.time() - start_time}s')
            if response.status_code == 200:
                res_to_dict = response.json()
                return res_to_dict
            else:
                SrvErrorHandler.default_handle('Chunk Error: retry number %s' % i)
                if i == 2:
                    SrvErrorHandler.default_handle('retry over 3 times')
                    SrvErrorHandler.default_handle(response.content)
                    # SrvErrorHandler.default_handle(response.content, True)

            # wait certain amount of time and retry
            # the time will be longer for more retry
            time.sleep(AppConfig.Env.resilient_retry_interval * (i + 1))

    @require_valid_token()
    def on_succeed(self):
        for i in range(AppConfig.Env.resilient_retry):
            url = self.base_url + '/v1/files'
            payload = uf.generate_on_success_form(
                self.project_code,
                self.operator,
                self.upload_form,
                [],
                process_pipeline=self.process_pipeline,
                upload_message=self.upload_message,
            )
            headers = {
                'Authorization': 'Bearer ' + self.user.access_token,
                'Refresh-token': self.user.refresh_token,
                'Session-ID': self.session_id,
            }
            # start_time = time.time()
            response = resilient_session().post(url, json=payload, headers=headers)
            # print(f'\napi {url} spent {time.time() - start_time}s')
            res_json = response.json()

            if res_json.get('code') == 200:
                # mhandler.SrvOutPutHandler.start_finalizing()
                result = res_json['result']
                return result
            else:
                SrvErrorHandler.default_handle('Combine Error: retry number %s' % i)
                SrvErrorHandler.default_handle(response.content)
                if i == 2:
                    SrvErrorHandler.default_handle('retry over 3 times')
                # SrvErrorHandler.default_handle(response.content, True)

            time.sleep(AppConfig.Env.resilient_retry_interval * (i + 1))

    @require_valid_token()
    def create_file_lineage(self, source_file):
        if source_file and self.zone == AppConfig.Env.core_zone:
            child_rel_path = self.upload_form.resumable_relative_path + '/' + self.upload_form.resumable_filename
            child_item = search_item(self.project_code, self.zone, child_rel_path, 'file', self.user.access_token)
            child_file = child_item['result']
            parent_file_geid = source_file['id']
            child_file_geid = child_file['id']
            lineage_event = {
                'input_id': parent_file_geid,
                'output_id': child_file_geid,
                'input_name': source_file['name'],
                'output_name': child_file['name'],
                'project_code': self.project_code,
                'pipeline_name': self.process_pipeline,
                'operator': self.operator,
                'token': self.user.access_token,
            }
            create_lineage(lineage_event)

    @require_valid_token()
    def check_status(self, converted_filename):
        url = AppConfig.Connections.url_status
        headers = {'Authorization': 'Bearer ' + self.user.access_token, 'Session-ID': self.session_id}
        query = {
            'action': 'data_upload',
            'project_code': self.project_code,
            'operator': self.operator,
            'session_id': self.session_id,
        }

        response = resilient_session().get(url, headers=headers, params=query)
        mhandler.SrvOutPutHandler.finalize_upload()
        if response.status_code == 200:
            result = response.json().get('result')
            for i in result:
                if i.get('source') == converted_filename and i.get('status') == 'SUCCEED':
                    mhandler.SrvOutPutHandler.upload_job_done()
                    return True
                elif i.get('source') == converted_filename and i.get('status') == 'TERMINATED':
                    SrvErrorHandler.customized_handle(ECustomizedError.FILE_EXIST, self.regular_file)
                elif i.get('source') == converted_filename and i.get('status') == 'CHUNK_UPLOADED':
                    return False
                else:
                    SrvErrorHandler.default_handle(response.content)
        else:
            return False


def compress_folder_to_zip(path):
    path = path.rstrip('/').lstrip()
    zipfile_path = path + '.zip'
    mhandler.SrvOutPutHandler.start_zipping_file()
    zipf = zipfile.ZipFile(zipfile_path, 'w', zipfile.ZIP_DEFLATED)
    for root, _, files in os.walk(path):
        for file in files:
            zipf.write(os.path.join(root, file))
    zipf.close()


def convert_filename(path, base_name, job_type, target_folder):
    file_name = os.path.basename(path)
    relative_file_path = os.path.relpath(path)
    if job_type == 'AS_FILE':
        if target_folder == '':
            converted_filename = file_name
        else:
            converted_filename = target_folder + '/' + file_name
        _relative_path = ''
    else:
        _base_file_name = relative_file_path.index(base_name)
        converted_filename = relative_file_path[_base_file_name:]
        end_index = relative_file_path.rindex(file_name) - 1
        _relative_path = relative_file_path[_base_file_name:end_index]
        if target_folder == '':
            pass
        else:
            converted_filename = target_folder + '/' + '/'.join(converted_filename.split('/')[1:])
    return converted_filename, _relative_path


def assemble_path(f, target_folder, project_code, zone, access_token, zipping=False):
    current_folder_node = target_folder + '/' + f.rstrip('/').split('/')[-1]
    result_file = current_folder_node
    name_folder = current_folder_node.split('/')[0].lower()
    name_folder_res = search_item(project_code, zone, name_folder, 'name_folder', access_token)
    name_folder_code = name_folder_res['code']
    name_folder_result = name_folder_res['result']
    if name_folder_code == 403:
        SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, True)
    elif not name_folder_result:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_NAMEFOLDER, True)
    if len(current_folder_node.split('/')) > 2:
        parent_path = name_folder + '/' + '/'.join(current_folder_node.split('/')[1:-1])
        res = search_item(project_code, zone, parent_path, 'folder', access_token)
        if not res['result']:
            click.confirm(customized_error_msg(ECustomizedError.CREATE_FOLDER_IF_NOT_EXIST), abort=True)
    if zipping:
        result_file = result_file + '.zip'
    return current_folder_node, result_file


def simple_upload(upload_event, num_of_thread: int = 1):
    upload_start_time = time.time()
    my_file = upload_event.get('file')
    project_code = upload_event.get('project_code')
    tags = upload_event.get('tags')
    zone = upload_event.get('zone')
    process_pipeline = upload_event.get('process_pipeline', None)
    upload_message = upload_event.get('upload_message')
    target_folder = upload_event.get('current_folder_node', '')
    compress_zip = upload_event.get('compress_zip', False)
    regular_file = upload_event.get('regular_file', True)
    source_file = upload_event.get('valid_source')
    attribute = upload_event.get('attribute')

    mhandler.SrvOutPutHandler.start_uploading(my_file)
    base_path = ''
    # if the input request zip folder then process the path as single file
    # otherwise read throught the folder to get path underneath
    if os.path.isdir(my_file):
        job_type = 'AS_FILE' if compress_zip else 'AS_FOLDER'
        if job_type == 'AS_FILE':
            upload_file_path = [my_file.rstrip('/').lstrip() + '.zip']
            target_folder = '/'.join(target_folder.split('/')[:-1]).rstrip('/')
            compress_folder_to_zip(my_file)
        else:
            logger.warn('Current version does not support folder tagging, ' 'any selected tags will be ignored')
            upload_file_path = get_file_in_folder(my_file)
            base_path = my_file.rstrip('/').split('/')[-1]
    else:
        job_type = 'AS_FILE'
        upload_file_path = [my_file]
        target_folder = '/'.join(target_folder.split('/')[:-1]).rstrip('/')

    # here add the batch of 500 per loop, the pre upload api cannot
    # process very large amount of file at same time. otherwise it
    # wil; timeout
    num_of_batchs = math.ceil(len(upload_file_path) / AppConfig.Env.upload_batch_size)
    # here is list of pre upload result. We decided to call pre upload api by batch
    # the result will store as (UploaderObject, preupload_id_mapping)
    # TODO: somehow here can be refactored
    pre_upload_info = []
    for batch in range(0, num_of_batchs):
        start_index = batch * AppConfig.Env.upload_batch_size
        end_index = (batch + 1) * AppConfig.Env.upload_batch_size
        file_batchs = upload_file_path[start_index:end_index]

        # prepare for the upload
        file_uploader = SrvSingleFileUploader(
            file_path=file_batchs,
            project_code=project_code,
            tags=tags,
            zone=zone,
            job_type=job_type,
            upload_message=upload_message,
            process_pipeline=process_pipeline,
            relative_path=base_path,
            current_folder_node=target_folder,
            regular_file=regular_file,
        )

        # sending the pre upload request to generate
        # the placeholder in object storage
        file_identities = file_uploader.pre_upload()
        pre_upload_info.append((file_uploader, file_identities))

    # then do the chunk upload/combine for each bach
    for (file_uploader, file_identities) in pre_upload_info:
        pool = ThreadPool(num_of_thread)

        def temp_upload_bundle(file_uploader: SrvSingleFileUploader):
            upload_start_time = time.time()
            file_uploader.generate_meta()

            file_uploader.stream_upload()
            upload_end_time = time.time()

            file_uploader.on_succeed()
            conbime_chunks_time = time.time()

            logger.info('chunk upload time spend: %.2f' % (upload_end_time - upload_start_time))
            logger.info('total time: %.2f' % (conbime_chunks_time - upload_start_time))
            logger.info('=============================================')

        # now loop over each file under the folder and start
        # the chunk upload
        for path in file_uploader.path:
            from copy import deepcopy

            t = deepcopy(file_uploader)
            t.user = file_uploader.user

            t.path = path
            t.upload_form.resumable_filename = os.path.basename(path)
            converted_filename, rel_path = convert_filename(path, base_path, job_type, target_folder)
            if target_folder == '':
                t.upload_form.resumable_relative_path = rel_path
            else:
                t.upload_form.resumable_relative_path = target_folder + '/' + '/'.join(rel_path.split('/')[1:])
            t.upload_form.resumable_identifier = file_identities.get(converted_filename)

            pool.apply_async(temp_upload_bundle, args=(t,))

            # file_uploader.generate_meta()

            # upload_start_time = time.time()
            # file_uploader.stream_upload()
            # upload_end_time = time.time()

            # file_uploader.on_succeed()
            # conbime_chunks_time = time.time()

            # logger.info('chunk upload time spend: %.2f' % (upload_end_time - upload_start_time))
            # logger.info('total time: %.2f' % (conbime_chunks_time - upload_start_time))

        pool.close()
        pool.join()

        if source_file or attribute:
            continue_loop = True
            while continue_loop:
                succeed = file_uploader.check_status(converted_filename)
                continue_loop = not succeed
                time.sleep(0.5)
            if source_file:
                file_uploader.create_file_lineage(source_file)
                os.remove(file_batchs[0]) if os.path.isdir(my_file) and job_type == 'AS_FILE' else None

        logger.info('Upload Time: %.2f' % (time.time() - upload_start_time))
