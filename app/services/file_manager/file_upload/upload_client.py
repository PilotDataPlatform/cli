# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import hashlib
import json
import math
import os
import time
from multiprocessing.pool import ApplyResult
from multiprocessing.pool import ThreadPool
from typing import Any

import httpx

import app.models.upload_form as uf
import app.services.output_manager.message_handler as mhandler
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.services.file_manager.file_upload.models import FileObject
from app.services.file_manager.file_upload.models import UploadType
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token
from app.services.user_authentication.token_manager import SrvTokenManager
from app.utils.aggregated import get_file_info_by_geid
from app.utils.aggregated import resilient_session
from app.utils.aggregated import search_item

from .exception import INVALID_CHUNK_ETAG
from ..file_lineage import create_lineage


class UploadClient:
    """
    Summary:
        The upload client is per upload base. it stores some immutable.
        infomation of particular upload action:
         - input_path: the path that user inputs. can be a folder or file.
         - project_code: the unique code of project.
         - zone: data zone. can be greenroom or core.
         - upload_message:
         - job_type: based on the input. can be AS_FILE or AS_FOLDER.
         - current_folder_node: the target folder in object storage.
    """

    def __init__(
        self,
        input_path: str,
        project_code: str,
        parent_folder_id: str,
        zone: str = AppConfig.Env.green_zone,
        upload_message: str = 'cli straight upload',
        job_type: str = UploadType.AS_FILE,
        process_pipeline: str = None,
        current_folder_node: str = '',
        regular_file: str = True,
        tags: list = None,
    ):
        self.user = UserConfig()
        self.operator = self.user.username
        self.input_path = input_path
        self.upload_message = upload_message
        self.chunk_size = AppConfig.Env.chunk_size
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
        self.current_folder_node = current_folder_node
        self.parent_folder_id = parent_folder_id
        self.regular_file = regular_file
        self.tags = tags

        self.finish_upload = False

    def generate_meta(self, local_path: str) -> tuple[int, int]:
        """
        Summary:
            The function is to generate chunk upload meatedata for a file.
        Parameter:
            - input_path: The path of the local file eg. a/b/c.txt.
        return:
            - total_size: the size of file.
            - total_chunks: the number of chunks will be uploaded.
        """
        file_length_in_bytes = os.path.getsize(local_path)
        total_size = file_length_in_bytes
        total_chunks = math.ceil(total_size / self.chunk_size)
        return total_size, total_chunks

    @require_valid_token()
    def resume_upload(self, unfinished_file_objects: list[FileObject]) -> list[FileObject]:
        """
        Summary:
            The function is to check the uploaded chunks in object storage.
        Parameter:
            - unfinished_file_objects(List[FileObject]): the unfinished items that need to be resumed.
        return:
            - list of FileObject: the infomation retrieved from backend.
                - resumable_id(str): the unique identifier for multipart upload.
                - object_path(str): the path in the object storage.
                - local_path(str): the local path of file.
                - chunk_info(dict): the mapping for chunks that already been uploaded.
        """
        mhandler.SrvOutPutHandler.resume_warning(len(unfinished_file_objects))

        headers = {'Authorization': 'Bearer ' + self.user.access_token, 'Session-ID': self.user.session_id}
        url = AppConfig.Connections.url_bff + f'/v1/project/{self.project_code}/files/resumable'
        rid_file_object_map = {x.resumable_id: x for x in unfinished_file_objects}
        payload = {
            'bucket': self.bucket,
            'zone': self.zone,
            'object_infos': [
                {
                    'object_path': file_object.object_path,
                    'item_id': file_object.item_id,
                    'resumable_id': file_object.resumable_id,
                }
                for file_object in unfinished_file_objects
            ],
        }

        response = resilient_session().post(url, json=payload, headers=headers, timeout=None)
        if response.status_code == 404:
            SrvErrorHandler.customized_handle(ECustomizedError.UPLOAD_ID_NOT_EXIST, True)

        uploaded_infos = response.json().get('result', [])
        for uploaded_info in uploaded_infos:
            file_obj = rid_file_object_map.get(uploaded_info.get('resumable_id'))
            file_obj.uploaded_chunks = uploaded_info.get('chunks_info')
        mhandler.SrvOutPutHandler.resume_check_success()

        return unfinished_file_objects

    @require_valid_token()
    def pre_upload(self, file_objects: list[FileObject], output_path: str) -> list[FileObject]:
        """
        Summary:
            The function is to initiate all the multipart upload.
        Parameter:
            - local_file_paths(list of str): the local path of files to be uploaded.
            - output_path(str): the output path of manifest.
        return:
            - list of FileObject: the infomation retrieved from backend.
                - resumable_id(str): the unique identifier for multipart upload.
                - object_path(str): the path in the object storage.
                - local_path(str): the local path of file.
                - chunk_info(dict): the mapping for chunks that already been uploaded.
        """

        headers = {'Authorization': 'Bearer ' + self.user.access_token, 'Session-ID': self.user.session_id}
        url = AppConfig.Connections.url_bff + f'/v1/project/{self.project_code}/files'
        payload = {
            'project_code': self.project_code,
            'operator': self.operator,
            'job_type': str(self.job_type),
            'zone': self.zone,
            'current_folder_node': self.current_folder_node,
            'parent_folder_id': self.parent_folder_id,
            'folder_tags': self.tags,
            'data': [
                {'resumable_filename': x.file_name, 'resumable_relative_path': x.parent_path} for x in file_objects
            ],
        }

        response = resilient_session().post(url, json=payload, headers=headers, timeout=None)

        if response.status_code == 200:
            result = response.json().get('result')
            file_mapping = {x.object_path: x for x in file_objects}
            file_objets = []
            for job in result:
                object_path = job.get('target_names')[0]
                # get the file object from mapping and update the attribute
                file_object = file_mapping.get(object_path)
                file_object.resumable_id = job.get('payload').get('resumable_identifier')
                file_object.item_id = job.get('payload').get('item_id')
                file_object.job_id = job.get('job_id')
                file_objets.append(file_object)

            # then output manifest file to the output path
            self.output_manifest(file_objets, output_path)

            mhandler.SrvOutPutHandler.preupload_success()
            return file_objets
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

    def output_manifest(self, file_objects: list[FileObject], output_path: str) -> dict[str, Any]:
        """
        Summary:
            The function is to output the manifest file.
        Parameter:
            - file_objects(list of FileObject): the file objects that contains correct
                information for chunk uploading.
        return:
            - manifest_json(dict): the manifest file in json format.
        """

        manifest_json = {
            'project_code': self.project_code,
            'operator': self.operator,
            'zone': self.zone,
            'parent_folder_id': self.parent_folder_id,
            'current_folder_node': self.current_folder_node,
            'tags': self.tags,
            'upload_message': self.upload_message,
            'file_objects': {file_object.item_id: file_object.to_dict() for file_object in file_objects},
        }

        with open(output_path, 'w') as f:
            json.dump(manifest_json, f)

        return manifest_json

    def stream_upload(self, file_object: FileObject, pool: ThreadPool) -> list[ApplyResult]:
        """
        Summary:
            The function is a wrap to display the uploading process.
            It will submit the async function job to ThreadPool. Each
            of chunk upload process will be queued in pool and scheduled.
        Parameter:
            - file_object(FileObject): the file object that contains correct
                information for chunk uploading.
        return:
            - List[ApplyResult]: the result of each chunk upload. and will be
                used in on_success function to make sure all the chunks have
                been uploaded.
        """
        count = 0

        # process on the file content
        f = open(file_object.local_path, 'rb')
        # this will be used to check if the chunk has been uploaded
        # in the on_success function. to make sure on_success is called
        # after all the chunks have been uploaded.
        chunk_result = []
        while True:
            chunk = f.read(self.chunk_size)
            chunk_etag = file_object.uploaded_chunks.get(str(count + 1))
            if not chunk:
                break
            # if current chunk has been uploaded to object storage
            # only check the md5 if the file is same. If ture,
            # skip current chunk, if not, raise the error.
            elif chunk_etag:
                local_chunk_etag = hashlib.md5(chunk).hexdigest()
                if chunk_etag != local_chunk_etag:
                    SrvErrorHandler.customized_handle(ECustomizedError.INVALID_CHUNK_UPLOAD, value=count + 1)
                    raise INVALID_CHUNK_ETAG(count + 1)
                file_object.update_progress(self.chunk_size)
            else:
                res = pool.apply_async(
                    self.upload_chunk,
                    args=(file_object, count + 1, chunk),
                )
                chunk_result.append(res)

            count += 1  # uploaded successfully

        f.close()

        return chunk_result

    def upload_chunk(self, file_object: FileObject, chunk_number: int, chunk: str) -> None:
        """
        Summary:
            The function is to upload a chunk directly into minio storage.
        Parameter:
            - file_object(FileObject): the file object that contains correct
                information for chunk uploading.
            - chunk_number(int): the number of current chunk.
            - chunk(str): the chunk data.
        return:
            - None
        """

        # retry three times
        for i in range(AppConfig.Env.resilient_retry):
            if i > 0:
                SrvErrorHandler.default_handle(f'retry number {i}')

            file_object.update_progress(0)

            # request upload service to generate presigned url for the chunk
            params = {
                'bucket': self.bucket,
                'key': file_object.object_path,
                'upload_id': file_object.resumable_id,
                'chunk_number': chunk_number,
            }
            headers = {'Authorization': 'Bearer ' + self.user.access_token, 'Session-ID': self.user.session_id}
            response = httpx.get(
                self.base_url + '/v1/files/chunks/presigned',
                params=params,
                headers=headers,
                timeout=None,
            )

            # then use the presigned url directly uplad to minio
            if response.status_code == 200:
                presigned_chunk_url = response.json().get('result')
                res = httpx.put(presigned_chunk_url, data=chunk, timeout=None)

                if res.status_code != 200:
                    error_msg = f'Fail to upload the chunck {chunk_number}: {str(res.text)}'
                    raise Exception(error_msg)

                # update the progress bar
                file_object.update_progress(len(chunk))
                if chunk_number == file_object.total_chunks:
                    file_object.close_progress()

                return res
            else:
                SrvErrorHandler.default_handle(f'Chunk Error: retry number {i}')
                if i == 2:
                    SrvErrorHandler.default_handle('retry over 3 times')
                    SrvErrorHandler.default_handle(response.content)

            # wait certain amount of time and retry
            # the time will be longer for more retry
            time.sleep(AppConfig.Env.resilient_retry_interval * (i + 1))

    def on_succeed(self, file_object: FileObject, tags: list[str], chunk_result: list[ApplyResult]) -> None:
        """
        Summary:
            The function is to finalize the upload process.
        Parameter:
            - file_object(FileObject): the file object that contains correct
                information for chunk uploading.
            - tags(list of str): the tag attached with uploaded object.
            - chunk_result(list of ApplyResult): the result of each chunk upload.
        return:
            - None
        """

        # check if all the chunks have been uploaded
        for res in chunk_result:
            while res.get() is None:
                time.sleep(1)

        for i in range(AppConfig.Env.resilient_retry):
            url = self.base_url + '/v1/files'
            payload = uf.generate_on_success_form(
                self.project_code,
                self.operator,
                file_object,
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
                SrvErrorHandler.default_handle(f'Combine Error: retry number {i}')
                SrvErrorHandler.default_handle(response.content)
                if i == 2:
                    SrvErrorHandler.default_handle('retry over 3 times')

            time.sleep(AppConfig.Env.resilient_retry_interval * (i + 1))

    @require_valid_token()
    def create_file_lineage(self, source_file: dict, new_file_object: FileObject):
        """
        Summary:
            The function is to create a lineage with source file.
        Parameter:
            - source_file(str): the file object that indicate the exist data to link with.
            - new_file_object(FileObject): the new object just uploaded.
        return:
            - bool: if job success or not.
        """

        if source_file and self.zone == AppConfig.Env.core_zone:
            child_rel_path = new_file_object.object_path
            child_item = search_item(self.project_code, self.zone, child_rel_path, 'file')
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

    def check_status(self, file_object: FileObject) -> bool:
        """
        Summary:
            The function is to check the status of upload process.
        Parameter:
            - file_object(FileObject): the file object that contains correct.
                information for chunk uploading.
        return:
            - bool: if job success or not
        """

        # with pre-register upload, we can check if the file entity is already exist
        # if exist, we can continue with manifest process
        file_entity = get_file_info_by_geid([file_object.item_id])[0].get('result', {})
        mhandler.SrvOutPutHandler.finalize_upload()
        if file_entity.get('status') == 'ACTIVE':
            return True
        else:
            return False

    def set_finish_upload(self):
        self.finish_upload = True

    def upload_token_refresh(self, azp: str = AppConfig.Env.keycloak_device_client_id):
        token_manager = SrvTokenManager()
        DEFAULT_INTERVAL = 2  # seconds to check if the upload is finished
        total_count = 0  # when total_count equals token_refresh_interval, refresh token
        while self.finish_upload is not True:
            if total_count >= AppConfig.Env.token_refresh_interval:
                token_manager.refresh(azp)
                total_count = 0

            # if not then sleep for DEFAULT_INTERVAL seconds
            time.sleep(DEFAULT_INTERVAL)
            total_count = total_count + DEFAULT_INTERVAL
