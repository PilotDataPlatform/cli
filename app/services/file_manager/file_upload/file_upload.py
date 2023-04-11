# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

import math
import os
import time
import zipfile
from multiprocessing.pool import ThreadPool
from typing import Dict
from typing import List
from typing import Tuple

import click

import app.services.logger_services.log_functions as logger
import app.services.output_manager.message_handler as mhandler
from app.configs.app_config import AppConfig
from app.services.file_manager.file_upload.models import FileObject
from app.services.file_manager.file_upload.models import UploadType
from app.services.file_manager.file_upload.upload_client import UploadClient
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.error_handler import customized_error_msg
from app.utils.aggregated import get_file_in_folder
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
    f: str, target_folder: str, project_code: str, zone: str, resumable_id: str, zipping: bool = False
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
         - resumable_id(str): the unique identifier of a upload process
         - zipping(bool): default False. The flag to indicate if upload as a zip
    Return:
         - current_file_path: the format file path on platform
         - parent_folder: the item information of longest parent folder
         - create_folder_flag: the flag to indicate if need to create new folder
         - result_file: the result file if zipping

    '''

    current_file_path = target_folder + '/' + f.rstrip('/').split('/')[-1]
    result_file = current_file_path

    # set name folder as first parent folder
    name_folder = current_file_path.split('/')[0]
    parent_folder = search_item(project_code, zone, name_folder, 'name_folder')
    parent_folder = parent_folder.get('result')
    create_folder_flag = False

    if len(current_file_path.split('/')) > 2 and not resumable_id:
        sub_path = target_folder.split('/')
        for index in range(len(sub_path) - 1):
            folder_path = '/'.join(sub_path[0 : 2 + index])
            res = search_item(project_code, zone, folder_path, 'folder')

            # find the longest existing folder as parent folder
            # if user input a path that need to create some folders
            if not res.get('result'):
                click.confirm(customized_error_msg(ECustomizedError.CREATE_FOLDER_IF_NOT_EXIST), abort=True)
                create_folder_flag = True
                break
            else:
                parent_folder = res.get('result')
    elif resumable_id:
        mhandler.SrvOutPutHandler.resume_warning(resumable_id)

    # error check if the user dont have permission to see the folder
    # because the name folder will always be there if user has correct permission
    if not parent_folder:
        SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, True)

    if zipping:
        result_file = result_file + '.zip'
    return current_file_path, parent_folder, create_folder_flag, result_file


def simple_upload(  # noqa: C901
    upload_event,
    num_of_thread: int = 1,
    resumable_id: str = None,
    job_id: str = None,
    item_id: str = None,
) -> List[FileObject]:
    upload_start_time = time.time()
    my_file = upload_event.get('file')
    project_code = upload_event.get('project_code')
    tags = upload_event.get('tags')
    zone = upload_event.get('zone')
    # process_pipeline = upload_event.get('process_pipeline', None)
    # upload_message = upload_event.get('upload_message')
    target_folder = upload_event.get('current_folder_node', '')
    parent_folder_id = upload_event.get('parent_folder_id', '')
    create_folder_flag = upload_event.get('create_folder_flag', False)
    compress_zip = upload_event.get('compress_zip', False)
    regular_file = upload_event.get('regular_file', True)
    source_file = upload_event.get('valid_source')
    # attribute = upload_event.get('attribute')

    mhandler.SrvOutPutHandler.start_uploading(my_file)
    # TODO: PILOT-2392 simplify the logic under
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
            logger.warning('Current version does not support folder tagging, ' 'any selected tags will be ignored')
            upload_file_path = get_file_in_folder(my_file)
    else:
        upload_file_path = [my_file]
        target_folder = '/'.join(target_folder.split('/')[:-1]).rstrip('/')

        if create_folder_flag:
            job_type = UploadType.AS_FOLDER
            my_file = os.path.dirname(my_file)  # update the path as folder
        else:
            job_type = UploadType.AS_FILE

    upload_client = UploadClient(
        input_path=my_file,
        project_code=project_code,
        zone=zone,
        job_type=job_type,
        current_folder_node=target_folder,
        parent_folder_id=parent_folder_id,
        regular_file=regular_file,
        tags=tags,
    )

    # here add the batch of 500 per loop, the pre upload api cannot
    # process very large amount of file at same time. otherwise it will timeout
    num_of_batchs = math.ceil(len(upload_file_path) / AppConfig.Env.upload_batch_size)
    # here is list of pre upload result. We decided to call pre upload api by batch
    # the result will store as (UploaderObject, preupload_id_mapping)
    pre_upload_infos = []

    # TODO later will adapt the folder resumable upload
    # for now it is only for file resumable
    if resumable_id and job_id:
        pre_upload_infos.extend(upload_client.resume_upload(resumable_id, job_id, item_id, upload_file_path[0]))
    else:
        for batch in range(0, num_of_batchs):
            start_index = batch * AppConfig.Env.upload_batch_size
            end_index = (batch + 1) * AppConfig.Env.upload_batch_size
            file_batchs = upload_file_path[start_index:end_index]

            # sending the pre upload request to generate
            # the placeholder in object storage
            pre_upload_infos.extend(upload_client.pre_upload(file_batchs))

    # now loop over each file under the folder and start
    # the chunk upload

    # thread number +1 reserve one thread to refresh token
    # and remove the token decorator in functions

    pool = ThreadPool(num_of_thread + 1)
    pool.apply_async(upload_client.upload_token_refresh)
    for file_object in pre_upload_infos:
        chunk_res = upload_client.stream_upload(file_object, pool)
        # NOTE: if there is some racing error make the combine chunks
        # out of thread pool.
        pool.apply_async(
            upload_client.on_succeed,
            args=(file_object, tags, chunk_res),
        )
    upload_client.set_finish_upload()

    pool.close()
    pool.join()

    if source_file:
        continue_loop = True
        while continue_loop:
            # the last uploaded file
            succeed = upload_client.check_status(file_object)
            continue_loop = not succeed
            time.sleep(0.5)
        if source_file:
            upload_client.create_file_lineage(source_file)
            os.remove(file_batchs[0]) if os.path.isdir(my_file) and job_type == UploadType.AS_FILE else None

    num_of_file = len(upload_file_path)
    logger.info(f'Upload Time: {time.time() - upload_start_time:.2f}s for {num_of_file:d} files')

    return pre_upload_infos
