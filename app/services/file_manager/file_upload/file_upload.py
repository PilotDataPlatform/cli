# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import math
import os
import time
import zipfile
from multiprocessing.pool import ThreadPool
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import click

import app.services.logger_services.log_functions as logger
import app.services.output_manager.message_handler as mhandler
from app.configs.app_config import AppConfig
from app.services.file_manager.file_upload.models import FileObject
from app.services.file_manager.file_upload.models import ItemStatus
from app.services.file_manager.file_upload.models import UploadType
from app.services.file_manager.file_upload.upload_client import UploadClient
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.error_handler import customized_error_msg
from app.utils.aggregated import get_file_in_folder
from app.utils.aggregated import get_file_info_by_geid
from app.utils.aggregated import search_item


def compress_folder_to_zip(path):
    path = path.rstrip('/').lstrip()
    zipfile_path = path + '.zip'
    mhandler.SrvOutPutHandler.start_zipping_file()
    zipf = zipfile.ZipFile(zipfile_path, 'w', zipfile.ZIP_DEFLATED)
    for root, _, files in os.walk(path):
        for file in files:
            zipf.write(os.path.join(root, file))
    zipf.close()


def assemble_path(
    f: str, target_folder: str, project_code: str, zone: str, zipping: bool = False
) -> Tuple[str, Dict, bool, str]:
    '''
    Summary:
        the function is to find the longest parent folder that exists
        in the backend. Since cli will allow user to specify the folder
        that is not exist yet. and let upload process to create them.
        By default, the parent folder will be name folder.

        also the function will format the local path with the target path.
        eg. path is folder1/file1(local) and target folder is admin/target1(on platform)
        the final path will be admin/target1/folder1/file1

    Parameter:
         - f(str): the local path of a file
         - target_folder(str): the folder on the platform
         - project_code(str): the unique identifier of project
         - zone(str): the zone label eg.greenroom/core
         - zipping(bool): default False. The flag to indicate if upload as a zip
    Return:
         - current_file_path: the format file path on platform
         - parent_folder: the item information of longest parent folder
         - create_folder_flag: the flag to indicate if need to create new folder
         - result_file: the result file if zipping

    '''

    current_file_path = target_folder + '/' + f.rstrip('/').split('/')[-1]
    result_file = current_file_path
    if zipping:
        result_file = result_file + '.zip'

    name_folder = target_folder.split('/')[0]
    parent_folder = search_item(project_code, zone, name_folder, 'name_folder')
    parent_folder = parent_folder.get('result')

    current_folder_node = target_folder if os.path.isfile(f) else current_file_path
    create_folder_flag = False
    if len(current_file_path.split('/')) > 2:
        sub_path = target_folder.split('/')
        for index in range(len(sub_path) - 1):
            folder_path = '/'.join(sub_path[0 : 2 + index])
            res = search_item(project_code, zone, folder_path, 'folder')

            if not res.get('result'):
                current_folder_node = folder_path
                click.confirm(customized_error_msg(ECustomizedError.CREATE_FOLDER_IF_NOT_EXIST), abort=True)
                create_folder_flag = True
                break
            else:
                parent_folder = res.get('result')

    if not parent_folder:
        SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, True)

    return current_folder_node, parent_folder, create_folder_flag, result_file


def simple_upload(  # noqa: C901
    upload_event,
    num_of_thread: int = 1,
    output_path: str = None,
) -> List[str]:
    upload_start_time = time.time()
    input_path = upload_event.get('file')
    project_code = upload_event.get('project_code')
    tags = upload_event.get('tags')
    zone = upload_event.get('zone')
    upload_message = upload_event.get('upload_message')
    current_folder_node = upload_event.get('current_folder_node', '')
    parent_folder_id = upload_event.get('parent_folder_id', '')
    create_folder_flag = upload_event.get('create_folder_flag', False)
    compress_zip = upload_event.get('compress_zip', False)
    regular_file = upload_event.get('regular_file', True)
    source_file = upload_event.get('valid_source')
    attribute = upload_event.get('attribute')

    mhandler.SrvOutPutHandler.start_uploading(input_path)
    if os.path.isdir(input_path):
        job_type = UploadType.AS_FILE if compress_zip else UploadType.AS_FOLDER
        if job_type == UploadType.AS_FILE:
            upload_file_path = [input_path.rstrip('/').lstrip() + '.zip']
            compress_folder_to_zip(input_path)
        elif tags or attribute:
            SrvErrorHandler.customized_handle(ECustomizedError.UNSUPPORT_TAG_MANIFEST, True)
        else:
            upload_file_path = get_file_in_folder(input_path)
    else:
        upload_file_path = [input_path]

        if create_folder_flag:
            job_type = UploadType.AS_FOLDER
            input_path = os.path.dirname(input_path)
        else:
            job_type = UploadType.AS_FILE

    upload_client = UploadClient(
        input_path=input_path,
        project_code=project_code,
        zone=zone,
        job_type=job_type,
        current_folder_node=current_folder_node,
        parent_folder_id=parent_folder_id,
        regular_file=regular_file,
        tags=tags,
        upload_message=upload_message,
    )

    file_objects = []
    target_folder = upload_event.get('target_folder', '')
    input_path = os.path.dirname(input_path)
    for file in upload_file_path:
        file_path_sub = file.replace(input_path + '/', '') if input_path else file
        object_path = os.path.join(target_folder, file_path_sub)
        file_objects.append(FileObject(object_path, file))

    num_of_batchs = math.ceil(len(file_objects) / AppConfig.Env.upload_batch_size)
    pre_upload_infos = []
    for batch in range(0, num_of_batchs):
        start_index = batch * AppConfig.Env.upload_batch_size
        end_index = (batch + 1) * AppConfig.Env.upload_batch_size
        file_batchs = file_objects[start_index:end_index]

        pre_upload_infos.extend(upload_client.pre_upload(file_batchs, output_path))

    pool = ThreadPool(num_of_thread + 1)
    pool.apply_async(upload_client.upload_token_refresh)
    on_success_res = []
    for file_object in pre_upload_infos:
        chunk_res = upload_client.stream_upload(file_object, pool)
        res = pool.apply_async(
            upload_client.on_succeed,
            args=(file_object, tags, chunk_res),
        )
        on_success_res.append(res)

    [res.wait() for res in on_success_res]
    upload_client.set_finish_upload()

    pool.close()
    pool.join()

    if source_file or attribute:
        continue_loop = True
        while continue_loop:
            succeed = upload_client.check_status(file_object)
            continue_loop = not succeed
            time.sleep(0.5)
        if source_file:
            upload_client.create_file_lineage(source_file)
            os.remove(file_batchs[0]) if os.path.isdir(input_path) and job_type == UploadType.AS_FILE else None

    num_of_file = len(upload_file_path)
    logger.info(f'Upload Time: {time.time() - upload_start_time:.2f}s for {num_of_file:d} files')

    return [file_object.item_id for file_object in pre_upload_infos]


def resume_upload(
    manifest_json: Dict[str, Any],
    num_of_thread: int = 1,
):
    """
    Summary:
        Resume upload from the manifest file
    Parameters:
        - manifest_json: the manifest json which store the upload information
        - num_of_thread: the number of thread to upload the file
    """
    upload_start_time = time.time()

    upload_client = UploadClient(
        input_path=manifest_json.get('file'),
        project_code=manifest_json.get('project_code'),
        zone=manifest_json.get('zone'),
        job_type='AS_FOLDER',
        current_folder_node=manifest_json.get('current_folder_node', ''),
        parent_folder_id=manifest_json.get('parent_folder_id', ''),
        tags=manifest_json.get('tags'),
    )

    item_ids = []
    all_files = manifest_json.get('file_objects')
    for item_id in all_files:
        item_ids.append(item_id)
    items = get_file_info_by_geid(item_ids)

    unfinished_items = []
    for x in items:
        if x.get('result').get('status') == ItemStatus.REGISTERED:
            file_info = all_files.get(x.get('result').get('id'))
            unfinished_items.append(
                FileObject(
                    file_info.get('object_path'),
                    file_info.get('local_path'),
                    file_info.get('resumable_id'),
                    file_info.get('job_id'),
                    file_info.get('item_id'),
                )
            )

    unfinished_items = upload_client.resume_upload(unfinished_items)

    pool = ThreadPool(num_of_thread + 1)
    pool.apply_async(upload_client.upload_token_refresh)
    on_success_res = []
    for file_object in unfinished_items:
        chunk_res = upload_client.stream_upload(file_object, pool)
        res = pool.apply_async(
            upload_client.on_succeed,
            args=(file_object, manifest_json.get('tags'), chunk_res),
        )
        on_success_res.append(res)

    [res.wait() for res in on_success_res]
    upload_client.set_finish_upload()

    pool.close()
    pool.join()

    num_of_file = len(unfinished_items)
    logger.info(f'Upload Time: {time.time() - upload_start_time:.2f}s for {num_of_file:d} files')
