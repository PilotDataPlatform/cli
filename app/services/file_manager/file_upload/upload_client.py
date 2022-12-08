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
from typing import List, Tuple

# import httpx
import requests
from tqdm import tqdm

import app.models.upload_form as uf
import app.services.output_manager.message_handler as mhandler
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.services.file_manager.file_upload.models import FileObject, UploadType
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import resilient_session, search_item

from ..file_lineage import create_lineage


class UploadClient:
    def __init__(
        self,
        input_path,
        project_code,
        # relative_path,
        zone=AppConfig.Env.green_zone,
        upload_message='cli straight upload',
        job_type=UploadType.AS_FILE,
        process_pipeline=None,
        current_folder_node='',
        regular_file=True,
    ):
        self.user = UserConfig()
        self.operator = self.user.username
        self.input_path = input_path
        self.upload_message = upload_message
        self.chunk_size = AppConfig.Env.chunk_size  # remove
        self.base_url = {
            AppConfig.Env.green_zone: AppConfig.Connections.url_upload_greenroom,
            AppConfig.Env.core_zone: AppConfig.Connections.url_upload_core,
        }.get(zone.lower())

        prefix = {
            AppConfig.Env.green_zone: AppConfig.Env.greenroom_bucket_prefix,
            AppConfig.Env.core_zone: AppConfig.Env.core_bucket_prefix,
        }.get(zone.lower())
        self.bucket = prefix + '-' + project_code

        self.zone = zone
        self.job_type = job_type
        self.project_code = project_code
        self.process_pipeline = process_pipeline
        # self.session_id = UserConfig().session_id
        # self.relative_path = relative_path
        # self.upload_form = uf.FileUploadForm()
        # self.upload_form.tags = tags
        # self.upload_form.uploader = self.user.username
        # self.upload_form.resumable_filename = [os.path.basename(self.path[0])] if job_type == 'AS_FILE' else self.path
        # self.upload_form.resumable_relative_path = relative_path
        self.current_folder_node = current_folder_node
        self.regular_file = regular_file

    def generate_meta(self, local_path: str) -> Tuple[int, int]:
        '''
        Summary:
            The function is to generate chunk upload meatedata for a file.
        Parameter:
            - input_path: The path of the local file eg. a/b/c.txt.
        return:
            - total_size: the size of file
            - total_chunks: the number of chunks will be uploaded.
        '''
        file_length_in_bytes = os.path.getsize(local_path)
        total_size = file_length_in_bytes
        total_chunks = math.ceil(total_size / self.chunk_size)
        # mhandler.SrvOutPutHandler.uploading_files(
        #     self.upload_form.uploader,
        #     self.project_code,
        #     self.upload_form.resumable_total_size,
        #     self.upload_form.resumable_total_chunks,
        #     self.upload_form.resumable_relative_path.strip('/'),
        # )
        return total_size, total_chunks

    @require_valid_token()
    def resume_upload(self, resumable_id: str):
        headers = {'Authorization': 'Bearer ' + self.user.access_token, 'Session-ID': self.session_id}
        uploaded_chunks = []

        url = 'http://localhost:5079/v1/files/resumable'
        object_path = os.path.join(self.current_folder_node, self.upload_form.resumable_filename[0])
        params = {
            'bucket': self.bucket,
            'object_path': object_path,
            'upload_id': resumable_id,
        }
        response = resilient_session().get(url, params=params, headers=headers, timeout=None)
        if response.status_code == 404:
            SrvErrorHandler.customized_handle(ECustomizedError.UPLOAD_ID_NOT_EXIST, True)

        uploaded_chunks = response.json().get('result', [])
        chunks_info = {}
        # restructure the chunk list to {<part_number>: <etag>}
        for chunk_info in uploaded_chunks:
            chunks_info.update({chunk_info.get('PartNumber'): chunk_info.get('ETag')})

        res = {object_path: {'resumable_id': resumable_id, 'uploaded_chunks': chunks_info}}
        # todo update to resumable success
        mhandler.SrvOutPutHandler.resume_check_success()
        return res

    @require_valid_token()
    def pre_upload(self, local_file_paths: List[str]) -> List[FileObject]:
        headers = {'Authorization': 'Bearer ' + self.user.access_token, 'Session-ID': self.user.session_id}

        url = AppConfig.Connections.url_bff + '/v1/project/{}/files'.format(self.project_code)
        # the file mapping is a dictionary that present the map from object storage path
        # with local file path. It will be used in chunk upload api.
        payload, file_mapping = uf.generate_pre_upload_form(
            self.project_code,
            self.operator,
            local_file_paths,
            self.input_path,
            zone=self.zone,
            job_type=self.job_type,
            current_folder=self.current_folder_node,
        )
        response = resilient_session().post(url, json=payload, headers=headers, timeout=None)

        if response.status_code == 200:
            result = response.json().get('result')
            res = []
            for job in result:
                object_path = job.get('source')
                resumable_id = job.get('payload').get('resumable_identifier')
                res.append(FileObject(resumable_id, object_path, file_mapping.get(object_path), {}))

            mhandler.SrvOutPutHandler.preupload_success()
            return res
        elif response.status_code == 403:
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

    def stream_upload(self, file_object: FileObject):
        count = 0
        remaining_size = file_object.total_size
        with tqdm(
            total=file_object.total_size,
            leave=True,
            bar_format='{desc} |{bar:30} {percentage:3.0f}% {remaining}',
        ) as bar:
            bar.set_description(
                'Uploading {} , resumable_id: {}'.format(file_object.file_name, file_object.resumable_id)
            )
            f = open(file_object.local_path, 'rb')
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                # if current chunk has been uploaded to object storage
                # TODO only check the md5 if the file is same. If ture,
                # skip current chunk, if not, raise the error.
                elif file_object.uploaded_chunks.get(count + 1):
                    # print(f"the chunk has been uploaded with etag {uploaded_chunks.get(count + 1)}")
                    pass
                else:
                    self.upload_chunk(file_object, count + 1, chunk)

                # update progress bar
                if self.chunk_size > remaining_size:
                    bar.update(remaining_size)
                else:
                    bar.update(self.chunk_size)
                count += 1  # uploaded successfully
                remaining_size = remaining_size - self.chunk_size
            f.close()

    @require_valid_token()
    def upload_chunk(self, file_object: FileObject, chunk_number: int, chunk: str):
        # retry three times
        for i in range(AppConfig.Env.resilient_retry):
            if i > 0:
                SrvErrorHandler.default_handle('retry number %s' % i)

            payload = uf.generate_chunk_form(
                self.project_code,
                self.operator,
                file_object.resumable_id,
                file_object.parent_path,
                file_object.file_name,
                chunk_number,
            )
            headers = {'Authorization': 'Bearer ' + self.user.access_token, 'Session-ID': self.user.session_id}
            files = {'chunk_data': chunk}
            response = requests.post(self.base_url + '/v1/files/chunks', data=payload, headers=headers, files=files)

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
    def on_succeed(self, file_object: FileObject, tags: List):
        for i in range(AppConfig.Env.resilient_retry):
            url = self.base_url + '/v1/files'
            payload = uf.generate_on_success_form(
                self.project_code,
                self.operator,
                file_object.resumable_id,
                file_object.file_name,
                file_object.parent_path,
                file_object.total_size,
                file_object.total_chunks,
                tags,
                [],
                process_pipeline=self.process_pipeline,
                upload_message=self.upload_message,
            )
            headers = {
                'Authorization': 'Bearer ' + self.user.access_token,
                'Refresh-token': self.user.refresh_token,
                'Session-ID': self.user.session_id,
            }
            response = resilient_session().post(url, json=payload, headers=headers)
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
                'input_path': os.path.join(source_file['parent_path'], source_file['name']),
                'output_path': os.path.join(child_file['parent_path'], child_file['name']),
                'project_code': self.project_code,
                'action_type': self.process_pipeline,
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
