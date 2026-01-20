# Copyright (C) 2022-2026 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import base64
import hashlib
import json
import math
import os
import threading
import time
from logging import getLogger
from multiprocessing.pool import ThreadPool
from typing import Any, Dict, List, Tuple
from uuid import UUID

import httpx
from httpx import HTTPStatusError

import app.services.output_manager.message_handler as mhandler
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.upload_form import generate_on_success_form
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.file_manager.file_upload.models import FileObject, UploadType
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import ItemStatus, batch_generator, get_file_info_by_geid

from .exception import INVALID_CHUNK_ETAG

logger = getLogger(__name__)


class UploadClient(BaseAuthClient):
    """
    Summary:
        The upload client is per upload base. it stores some immutable.
        infomation of particular upload action:
         - project_code: the unique code of project.
         - zone: data zone. can be greenroom or core.
         - job_type: based on the input. can be AS_FILE or AS_FOLDER.
         - current_folder_node: the target folder in object storage.
    """

    def __init__(
        self,
        project_code: str,
        parent_folder_id: str,
        zone: str = AppConfig.Env.green_zone,
        job_type: str = UploadType.AS_FILE,
        current_folder_node: str = '',
        regular_file: str = True,
        tags: list = None,
        source_id: list[UUID] = '',
        attributes: dict = None,
    ):
        super().__init__('', timeout=60)

        self.user = UserConfig()
        self.operator = self.user.username
        self.chunk_size = AppConfig.Env.chunk_size

        prefix = {
            AppConfig.Env.green_zone: AppConfig.Env.greenroom_bucket_prefix,
            AppConfig.Env.core_zone: AppConfig.Env.core_bucket_prefix,
        }.get(zone.lower())
        self.bucket = prefix + '-' + project_code

        self.zone = zone
        self.job_type = job_type
        self.project_code = project_code
        self.current_folder_node = current_folder_node
        self.parent_folder_id = parent_folder_id
        self.regular_file = regular_file
        # tags and souce_id are only allowed in file uplaod
        self.tags = tags
        self.source_id = source_id
        self.attributes = attributes

        # the flag to indicate if all upload process finished
        # then the token refresh loop will end
        self.finish_upload = False

        # for tracking the multi-threading chunk upload
        self.active_jobs = 0
        self.lock = threading.Lock()

    def generate_meta(self, local_path: str) -> Tuple[int, int]:
        """
        Summary:
            The function is to generate chunk upload meatedata for a file.
        Parameter:
            - local_path: The path of the local file eg. a/b/c.txt.
        return:
            - total_size: the size of file.
            - total_chunks: the number of chunks will be uploaded.
        """
        file_length_in_bytes = os.path.getsize(local_path)
        total_size = file_length_in_bytes
        total_chunks = math.ceil(total_size / self.chunk_size)
        return total_size, total_chunks

    @require_valid_token()
    def resume_upload(self, unfinished_file_objects: List[FileObject]) -> List[FileObject]:
        """
        Summary:
            The function is to check the uploaded chunks in object storage.
        Parameter:
            - unfinished_file_objects(List[FileObject]): the unfinished items that need to be resumed.
        return:
            - list of FileObject: the information retrieved from backend.
                - resumable_id(str): the unique identifier for multipart upload.
                - object_path(str): the path in the object storage.
                - local_path(str): the local path of file.
                - chunk_info(dict): the mapping for chunks that already been uploaded.
        """

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

        try:
            self.endpoint = AppConfig.Connections.url_bff + '/v1'
            response = self._post(f'project/{self.project_code}/files/resumable', json=payload)
        except HTTPStatusError as e:
            response = e.response
            if response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.UPLOAD_ID_NOT_EXIST, True)
            else:
                SrvErrorHandler.default_handle('Error when resuming upload', True)

        # make the response into file objects
        uploaded_infos = response.json().get('result', [])
        for uploaded_info in uploaded_infos:
            file_obj = rid_file_object_map.get(uploaded_info.get('resumable_id'))
            # update the chunk info
            file_obj.uploaded_chunks = uploaded_info.get('chunks_info')

        return unfinished_file_objects

    @require_valid_token()
    def check_upload_duplication(
        self, file_objects: List[FileObject]
    ) -> Tuple[List[FileObject], List[str], List[Dict[str, Any]]]:
        """
        Summary:
            The function will call the api to check if the file has been uploaded.
            if yes, it will skip the file.
        Parameter:
            - file_objects(List[FileObject]): the file will be uploaded.
        return:
            - non_exist_file_objects(List[FileObject]): the file that need to be uploaded.
            - exist_files(List[str]): the file that has been uploaded. will be skipped
            - [updated] registered_file_objects(List[Dict[str, Any]]): this is to handle the conner case
                where upload interrupted at specific batch. The local json manifest mismatches with
                backend metadata. So we need to return the registered file objects as well if possible.
        """

        # generate a list of locations for uploaded files to check duplication
        # at same time, generate a dict of mapping with object_path: FileObject
        locations = [x.object_path for x in file_objects]
        object_path_file_object_map = {x.object_path.lower(): x for x in file_objects}

        payload = {
            'locations': locations,
            'container_code': self.project_code,
            'container_type': 'project',
            'zone': 0 if self.zone == 'greenroom' else 1,
        }
        try:
            self.endpoint = AppConfig.Connections.url_bff + '/v2'
            response = self._post('items/batch/exists', json=payload)
        except HTTPStatusError as e:
            response = e.response
            if response.status_code == 403:
                SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, self.regular_file)
            else:
                SrvErrorHandler.default_handle('Error when checking file duplication', True)

        # filter out the ACTIVE items and REGISTERED items from return
        exist_items = response.json().get('result', [])
        active_path, registered_items = [], []
        for item in exist_items:
            object_path = item.get('parent_path', '') + '/' + item.get('name', '')
            object_path_file_object_map.pop(object_path.lower(), None)
            if item.get('status') == ItemStatus.ACTIVE:
                active_path.append(object_path)
            else:
                registered_items.append(item)

        # reconstruct non exist file objects which will be uploaded
        # without lower() function.
        return_list = {}
        for _, item in object_path_file_object_map.items():
            return_list.update({item.object_path: item})

        return list(object_path_file_object_map.values()), active_path, registered_items

    @require_valid_token()
    def pre_upload(self, file_objects: List[FileObject]) -> List[FileObject]:
        """
        Summary:
            The function is to initiate all the multipart upload.
        Parameter:
            - local_file_paths(list of str): the local path of files to be uploaded.
        return:
            - list of FileObject: the infomation retrieved from backend.
                - resumable_id(str): the unique identifier for multipart upload.
                - object_path(str): the path in the object storage.
                - local_path(str): the local path of file.
                - chunk_info(dict): the mapping for chunks that already been uploaded.
        """

        payload = {
            'project_code': self.project_code,
            'operator': self.operator,
            'job_type': str(self.job_type),
            'zone': self.zone,
            'current_folder_node': self.current_folder_node,
            'parent_folder_id': self.parent_folder_id,
            'folder_tags': self.tags,
            'data': [
                {'resumable_filename': x.file_name, 'resumable_relative_path': x.parent_path, 'size': x.total_size}
                for x in file_objects
            ],
        }
        if self.source_id:
            payload.update({'source_id': self.source_id})
        if self.attributes:
            payload.update({'attributes_template': self.attributes})

        try:
            self.endpoint = AppConfig.Connections.url_bff + '/v1'
            response = self._post(f'project/{self.project_code}/files', json=payload)
        except HTTPStatusError as e:
            response = e.response
            if response.status_code == 403:
                SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, self.regular_file)
            elif response.status_code == 409:
                SrvErrorHandler.customized_handle(ECustomizedError.FILE_EXIST, self.regular_file)
            elif response.status_code == 400:
                SrvErrorHandler.customized_handle(ECustomizedError.FILE_LOCKED, True)
            elif response.status_code == 422:
                error_message = response.json().get('error_msg', {}).get('details')
                SrvErrorHandler.customized_handle(ECustomizedError.INVALID_ATTRIBUTE, True, value=error_message)
            else:
                SrvErrorHandler.default_handle(response.content, True)

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

        mhandler.SrvOutPutHandler.preupload_success()
        return file_objets

    def output_manifest(
        self, registered_items: List[FileObject], unregistered_items: List[FileObject], output_path: str
    ) -> Dict[str, Any]:
        """
        Summary:
            The function is to output the manifest file.
        Parameter:
            - registered_items(list of FileObject): the file object that has been registered
                in metadata service.
            - unregistered_items(list of FileObject): the file object that has not been registered
                and still need to pass thought preupload
            - output_path(str): the output path of manifest.
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
            'registered_items': {file_object.item_id: file_object.to_dict() for file_object in registered_items},
            'unregistered_items': {
                file_object.object_path: file_object.to_dict() for file_object in unregistered_items
            },
            'attributes': self.attributes if self.attributes else {},
            'resumable_manifest_file': output_path,
        }

        with open(output_path, 'w') as f:
            json.dump(manifest_json, f)

        return manifest_json

    def stream_upload(self, file_object: FileObject, pool: ThreadPool) -> None:
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
        semaphore = threading.Semaphore(pool._processes + 1)
        chunk_upload_done = threading.Event()

        def on_complete(result):
            semaphore.release()
            with self.lock:
                self.active_jobs -= 1
                if self.active_jobs == 0:
                    chunk_upload_done.set()

        # process on the file content
        f = open(file_object.local_path, 'rb')
        # this will be used to check if the chunk has been uploaded
        # in the on_success function. to make sure on_success is called
        # after all the chunks have been uploaded.
        while True:
            chunk_info = file_object.uploaded_chunks.get(str(count + 1), {})
            chunk_etag = chunk_info.get('etag')

            chunk = f.read(self.chunk_size)
            local_chunk_etag = base64.b64encode(hashlib.md5(chunk).digest()).decode('utf-8')
            if not chunk:
                break
            # if current chunk has been uploaded to object storage
            # only check the md5 if the file is same. If ture,
            # skip current chunk, if not, raise the error.
            elif chunk_etag:
                if chunk_etag != local_chunk_etag:
                    SrvErrorHandler.customized_handle(ECustomizedError.INVALID_CHUNK_UPLOAD, value=count + 1)
                    raise INVALID_CHUNK_ETAG(count + 1)
                chunk_size = chunk_info.get('chunk_size', self.chunk_size)
                file_object.update_progress(chunk_size)
            else:
                # let the semaphore to control the number of concurrent jobs
                # and the upload client to detect if upload finished
                semaphore.acquire()
                with self.lock:
                    self.active_jobs += 1

                pool.apply_async(
                    self.upload_chunk,
                    args=(file_object, count + 1, chunk, local_chunk_etag, len(chunk)),
                    callback=on_complete,
                )

            count += 1

        # for resumable check ONLY if user resume the upload at 100%
        # just check if there is any active job, if not, set the event
        while not chunk_upload_done.wait(timeout=5):
            if self.active_jobs == 0:
                chunk_upload_done.set()
            else:
                logger.warning('Waiting for all the chunks to be uploaded, remaining jobs: %s', self.active_jobs)

        f.close()

    def upload_chunk(self, file_object: FileObject, chunk_number: int, chunk: str, etag: str, chunk_size: int) -> None:
        """
        Summary:
            The function is to upload a chunk directly into minio storage.
        Parameter:
            - file_object(FileObject): the file object that contains correct
                information for chunk uploading.
            - chunk_number(int): the number of current chunk.
            - chunk(str): the chunk data.
            - etag(str): the md5 of chunk data.
        return:
            - None
        """

        file_object.update_progress(0)

        # request upload service to generate presigned url for the chunk
        params = {
            'bucket': self.bucket,
            'key': file_object.item_id,
            'upload_id': file_object.resumable_id,
            'chunk_number': chunk_number,
            'chunk_size': chunk_size,
        }
        headers = {
            'Content-MD5': etag,
        }
        try:
            self.endpoint = {
                AppConfig.Env.green_zone: AppConfig.Connections.url_fileops_greenroom + '/v1',
                AppConfig.Env.core_zone: AppConfig.Connections.url_fileops_core + '/v1',
            }.get(self.zone.lower())
            response = self._get('upload/chunks/presigned', params=params, headers=headers)
            presigned_chunk_url = response.json().get('result')

            headers = {
                'Content-MD5': etag,
            }
            res = httpx.put(presigned_chunk_url, data=chunk, timeout=None, headers=headers)
            res.raise_for_status()

        except HTTPStatusError as e:
            response = e.response
            logger.error(response.content)
            SrvErrorHandler.default_handle(response.content, True)

        # update the progress bar
        file_object.update_progress(len(chunk))
        if chunk_number == file_object.total_chunks:
            file_object.close_progress()

        return res

    def on_succeed(self, file_object: FileObject) -> None:
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

        payload = generate_on_success_form(
            self.project_code,
            self.operator,
            file_object,
            [],
        )
        try:
            self.endpoint = {
                AppConfig.Env.green_zone: AppConfig.Connections.url_fileops_greenroom + '/v1',
                AppConfig.Env.core_zone: AppConfig.Connections.url_fileops_core + '/v1',
            }.get(self.zone.lower())

            response = self._post('upload/chunks/combine', json=payload)
        except HTTPStatusError as e:
            response = e.response
            SrvErrorHandler.default_handle(response.content, True)

        result = response.json().get('result')
        return result

    def check_status(self, file_objects: list[FileObject]) -> list[FileObject]:
        """
        Summary:
            The function is to check the status of upload process.
        Parameter:
            - file_object(FileObject): the file object that contains correct.
                information for chunk uploading.
        return:
            - bool: if job success or not
        """

        file_ids = [file_object.item_id for file_object in file_objects]
        results = get_file_info_by_geid(file_ids)
        unfinished_files = []
        for r in results:
            status = r.get('status')
            if status != ItemStatus.ACTIVE:
                unfinished_files.append(r.get('result'))

        return unfinished_files

    def upload_status_check(self, file_objects: list[FileObject]) -> None:
        '''
        Summary:
            The function is to check the list of upload status.

        Parameter:
            - file_objects(list[FileObject]): the list of file objects that need to be checked.

        '''

        unfinished_files = file_objects
        wait_count = 0
        while len(unfinished_files) > 0:
            temp = []
            if wait_count % AppConfig.Env.output_truncate_count == 0:
                mhandler.SrvOutPutHandler.finalize_upload()
            elif wait_count > AppConfig.Env.max_waiting_count:
                SrvErrorHandler.customized_handle(ECustomizedError.UPLOAD_TIMEOUT, True)

            for file_batchs in batch_generator(file_objects, batch_size=AppConfig.Env.upload_batch_size):
                temp.extend(self.check_status(file_batchs))
            unfinished_files = temp
            wait_count += 1
            time.sleep(1)

        return

    def set_finish_upload(self):
        self.finish_upload = True
