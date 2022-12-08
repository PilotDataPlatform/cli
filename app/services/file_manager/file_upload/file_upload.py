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

import app.services.logger_services.log_functions as logger
import app.services.output_manager.message_handler as mhandler
from app.configs.app_config import AppConfig
from app.services.file_manager.file_upload.models import FileObject, UploadType
from app.services.file_manager.file_upload.upload_client import UploadClient
from app.services.output_manager.error_handler import (
    ECustomizedError,
    SrvErrorHandler,
    customized_error_msg,
)
from app.utils.aggregated import search_item

from ....utils.aggregated import get_file_in_folder


def compress_folder_to_zip(path):
    path = path.rstrip('/').lstrip()
    zipfile_path = path + '.zip'
    mhandler.SrvOutPutHandler.start_zipping_file()
    zipf = zipfile.ZipFile(zipfile_path, 'w', zipfile.ZIP_DEFLATED)
    for root, _, files in os.walk(path):
        for file in files:
            zipf.write(os.path.join(root, file))
    zipf.close()


def assemble_path(f, target_folder, project_code, zone, access_token, resumable_id, zipping=False):
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
        if not res['result'] and not resumable_id:
            click.confirm(customized_error_msg(ECustomizedError.CREATE_FOLDER_IF_NOT_EXIST), abort=True)
        elif resumable_id:
            mhandler.SrvOutPutHandler.resume_warning(resumable_id)
    if zipping:
        result_file = result_file + '.zip'
    return current_folder_node, result_file


def simple_upload(upload_event, num_of_thread: int = 1, resumable_id: str = None):
    upload_start_time = time.time()
    my_file = upload_event.get('file')
    project_code = upload_event.get('project_code')
    tags = upload_event.get('tags')
    zone = upload_event.get('zone')
    # process_pipeline = upload_event.get('process_pipeline', None)
    # upload_message = upload_event.get('upload_message')
    target_folder = upload_event.get('current_folder_node', '')
    compress_zip = upload_event.get('compress_zip', False)
    regular_file = upload_event.get('regular_file', True)
    source_file = upload_event.get('valid_source')
    attribute = upload_event.get('attribute')

    mhandler.SrvOutPutHandler.start_uploading(my_file)
    # base_path = ''
    # if the input request zip folder then process the path as single file
    # otherwise read throught the folder to get path underneath
    if os.path.isdir(my_file):
        job_type = UploadType.AS_FILE if compress_zip else UploadType.AS_FOLDER
        if job_type == UploadType.AS_FILE:
            upload_file_path = [my_file.rstrip('/').lstrip() + '.zip']
            target_folder = '/'.join(target_folder.split('/')[:-1]).rstrip('/')
            compress_folder_to_zip(my_file)
        elif job_type == UploadType.AS_FOLDER and resumable_id:
            SrvErrorHandler.customized_handle(ECustomizedError.UNSUPPORTED_PROJECT, True, project_code)
        else:
            logger.warn('Current version does not support folder tagging, ' 'any selected tags will be ignored')
            upload_file_path = get_file_in_folder(my_file)
            # base_path = my_file.rstrip('/').split('/')[-1]
    else:
        job_type = UploadType.AS_FILE
        upload_file_path = [my_file]
        target_folder = '/'.join(target_folder.split('/')[:-1]).rstrip('/')

    upload_client = UploadClient(
        input_path=my_file,
        project_code=project_code,
        zone=zone,
        # relative_path=target_folder,
        job_type=job_type,
        current_folder_node=target_folder,
        regular_file=regular_file,
    )

    # here add the batch of 500 per loop, the pre upload api cannot
    # process very large amount of file at same time. otherwise it will timeout
    num_of_batchs = math.ceil(len(upload_file_path) / AppConfig.Env.upload_batch_size)
    # here is list of pre upload result. We decided to call pre upload api by batch
    # the result will store as (UploaderObject, preupload_id_mapping)
    pre_upload_infos = []

    # TODO later will adapt the folder resumable upload
    # for now it is only for file resumable
    if resumable_id:
        pre_upload_infos.extend(upload_client.resume_upload(resumable_id, upload_file_path[0]))
    else:
        for batch in range(0, num_of_batchs):
            start_index = batch * AppConfig.Env.upload_batch_size
            end_index = (batch + 1) * AppConfig.Env.upload_batch_size
            file_batchs = upload_file_path[start_index:end_index]

            # sending the pre upload request to generate
            # the placeholder in object storage
            pre_upload_infos.extend(upload_client.pre_upload(file_batchs))

    # then do the chunk upload/combine for each bach
    pool = ThreadPool(num_of_thread)

    def multithread_upload(client: UploadClient, file_object: FileObject, tags):
        client.stream_upload(file_object)
        client.on_succeed(file_object, tags)

    # now loop over each file under the folder and start
    # the chunk upload
    for file_object in pre_upload_infos:
        pool.apply_async(
            multithread_upload,
            args=(
                upload_client,
                file_object,
                tags,
            ),
        )

    pool.close()
    pool.join()

    if source_file or attribute:
        continue_loop = True
        while continue_loop:
            # the last uploaded file
            succeed = upload_client.check_status(file_object.object_path)
            continue_loop = not succeed
            time.sleep(0.5)
        if source_file:
            upload_client.create_file_lineage(source_file)
            os.remove(file_batchs[0]) if os.path.isdir(my_file) and job_type == UploadType.AS_FILE else None

    num_of_file = len(upload_file_path)
    logger.info('Upload Time: %.2fs for %d files ' % (time.time() - upload_start_time, num_of_file))
