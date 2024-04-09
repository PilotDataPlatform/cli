# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import os
import time
import zipfile
from multiprocessing.pool import ThreadPool
from sys import exit
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import click
from click.exceptions import Abort

import app.services.logger_services.log_functions as logger
import app.services.output_manager.message_handler as mhandler
from app.configs.app_config import AppConfig
from app.models.item import ItemType
from app.services.file_manager.file_upload.models import FileObject
from app.services.file_manager.file_upload.models import ItemStatus
from app.services.file_manager.file_upload.models import UploadType
from app.services.file_manager.file_upload.upload_client import UploadClient
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.error_handler import customized_error_msg
from app.utils.aggregated import batch_generator
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
    f: str, target_folder: str, project_code: str, folder_type: ItemType, zone: str
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
    Return:
         - current_file_path: the format file path on platform
         - parent_folder: the item information of longest parent folder
         - create_folder_flag: the flag to indicate if need to create new folder
         - target_folder: result object path on platform

    '''

    current_file_path = target_folder + '/' + f.rstrip('/').split('/')[-1]
    # set name folder as first parent folder
    root_folder = target_folder.split('/')[0]
    parent_folder = search_item(project_code, zone, root_folder).get('result', {})

    # if f input is a file then current_folder_node is target_folder
    # otherwise it is target_folder + f input name
    current_folder_node = target_folder if os.path.isfile(f) else current_file_path
    create_folder_flag = False
    # add prefix to folder
    current_folder_node = folder_type.get_prefix_by_type() + current_folder_node
    target_folder = folder_type.get_prefix_by_type() + target_folder

    if len(current_file_path.split('/')) > 2:
        sub_path = target_folder.split('/')
        for index in range(len(sub_path) - 1):
            folder_path = '/'.join(sub_path[0 : 2 + index])
            res = search_item(project_code, zone, folder_path)

            # find the longest existing folder as parent folder
            # if user input a path that need to create some folders
            if not res.get('result'):
                try:
                    click.confirm(customized_error_msg(ECustomizedError.CREATE_FOLDER_IF_NOT_EXIST), abort=True)
                except Abort:
                    mhandler.SrvOutPutHandler.cancel_upload()
                    exit(1)

                # stop scaning and use the current folder as parent folder
                current_folder_node = folder_path
                create_folder_flag = True
                break
            else:
                parent_folder = res.get('result')

    # error check if the user dont have permission to see the folder
    # because the name folder will always be there if user has correct permission
    if not parent_folder:
        SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, True)

    return current_folder_node, parent_folder, create_folder_flag, target_folder


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
    # process_pipeline = upload_event.get('process_pipeline', None)
    upload_message = upload_event.get('upload_message')
    current_folder_node = upload_event.get('current_folder_node', '')
    parent_folder_id = upload_event.get('parent_folder_id', '')
    create_folder_flag = upload_event.get('create_folder_flag', False)
    compress_zip = upload_event.get('compress_zip', False)
    regular_file = upload_event.get('regular_file', True)
    source_id = upload_event.get('source_id', '')
    attribute = upload_event.get('attribute')

    mhandler.SrvOutPutHandler.start_uploading(input_path)
    # if the input request zip folder then process the path as single file
    # otherwise read throught the folder to get path underneath
    if os.path.isdir(input_path):
        job_type = UploadType.AS_FILE if compress_zip else UploadType.AS_FOLDER
        if job_type == UploadType.AS_FILE:
            upload_file_path = [input_path.rstrip('/').lstrip() + '.zip']
            compress_folder_to_zip(input_path)
        elif tags or attribute or source_id:
            SrvErrorHandler.customized_handle(ECustomizedError.UNSUPPORT_TAG_MANIFEST, True)
        else:
            upload_file_path = get_file_in_folder(input_path)
    else:
        upload_file_path = [input_path]

        if create_folder_flag:
            job_type = UploadType.AS_FOLDER
        else:
            job_type = UploadType.AS_FILE

    upload_client = UploadClient(
        project_code=project_code,
        zone=zone,
        job_type=job_type,
        current_folder_node=current_folder_node,
        parent_folder_id=parent_folder_id,
        regular_file=regular_file,
        tags=tags,
        source_id=source_id,
        upload_message=upload_message,
        attributes=attribute,
    )

    # format the local path into object storage path for preupload
    file_objects = []
    target_folder = upload_event.get('target_folder', '')
    input_path = os.path.dirname(input_path)
    for file in upload_file_path:
        # first remove the input path from the file path
        file_path_sub = file.replace(input_path + '/', '') if input_path else file
        object_path = os.path.join(target_folder, file_path_sub)

        # generate a placeholder for each file
        file_object = FileObject(object_path, file)
        # skip the file with 0 size
        if file_object.total_size == 0:
            logger.warning(f'Skip the file with 0 size: {file_object.file_name}')
        else:
            file_objects.append(file_object)

    # make the file duplication check to allow folde merging
    non_duplicate_file_objects = []
    if create_folder_flag is True:
        non_duplicate_file_objects = file_objects
    else:
        mhandler.SrvOutPutHandler.file_duplication_check()
        duplicated_file = []
        for file_batchs in batch_generator(file_objects, batch_size=AppConfig.Env.upload_batch_size):
            non_duplicates, duplicate_path = upload_client.check_upload_duplication(file_batchs)
            non_duplicate_file_objects.extend(non_duplicates)
            duplicated_file.extend(duplicate_path)

        if len(non_duplicate_file_objects) == 0:
            mhandler.SrvOutPutHandler.file_duplication_check_warning_with_all_same()
            SrvErrorHandler.customized_handle(ECustomizedError.UPLOAD_CANCEL, if_exit=True)
        elif len(duplicated_file) > 0:
            mhandler.SrvOutPutHandler.file_duplication_check_success()
            duplicate_warning_format = '\n'.join(duplicated_file)
            try:
                click.confirm(
                    customized_error_msg(ECustomizedError.UPLOAD_SKIP_DUPLICATION) % (duplicate_warning_format),
                    abort=True,
                )
            except Abort:
                mhandler.SrvOutPutHandler.cancel_upload()
                exit(1)

    # here is list of pre upload result. We decided to call pre upload api by batch
    pre_upload_infos = []
    for file_batchs in batch_generator(non_duplicate_file_objects, batch_size=AppConfig.Env.upload_batch_size):
        # sending the pre upload request to generate
        # the placeholder in object storage
        pre_upload_infos.extend(upload_client.pre_upload(file_batchs, output_path))

    # then output manifest file to the output path
    upload_client.output_manifest(pre_upload_infos, output_path)

    # now loop over each file under the folder and start
    # the chunk upload

    # thread number +1 reserve one thread to refresh token
    # and remove the token decorator in functions

    pool = ThreadPool(num_of_thread + 1)
    pool.apply_async(upload_client.upload_token_refresh)
    on_success_res = []

    file_object: FileObject
    for file_object in pre_upload_infos:
        chunk_res = upload_client.stream_upload(file_object, pool)
        # the on_success api will be called after all chunk uploaded
        res = pool.apply_async(
            upload_client.on_succeed,
            args=(file_object, tags, chunk_res),
        )
        on_success_res.append(res)

    # finish the upload once all on success api return
    # otherwise wait for 1 second and check again
    [res.wait() for res in on_success_res]
    upload_client.set_finish_upload()

    pool.close()
    pool.join()

    if attribute:
        continue_loop = True
        while continue_loop:
            # the last uploaded file
            succeed = upload_client.check_status(file_object)
            continue_loop = not succeed
            time.sleep(0.5)

    num_of_file = len(pre_upload_infos)
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
        project_code=manifest_json.get('project_code'),
        zone=manifest_json.get('zone'),
        job_type='AS_FOLDER',
        current_folder_node=manifest_json.get('current_folder_node', ''),
        parent_folder_id=manifest_json.get('parent_folder_id', ''),
        tags=manifest_json.get('tags'),
    )

    # check files in manifest if some of them are already uploaded
    unfinished_items = []
    all_files = manifest_json.get('file_objects')
    item_ids = []
    for item_id in all_files:
        item_ids.append(item_id)

    # here add the batch of 500 per loop, the pre upload api cannot
    # process very large amount of file at same time. otherwise it will timeout
    # here is list of pre upload result. We decided to call pre upload api by batch
    for file_batchs in batch_generator(item_ids, batch_size=AppConfig.Env.upload_batch_size):
        items = get_file_info_by_geid(file_batchs)

        # get the detail of item to see if the file is already uploaded
        unfinished_files = []
        for x in items:
            if x.get('result').get('status') == ItemStatus.REGISTERED:
                file_info = all_files.get(x.get('result').get('id'))
                unfinished_files.append(
                    FileObject(
                        file_info.get('object_path'),
                        file_info.get('local_path'),
                        file_info.get('resumable_id'),
                        file_info.get('job_id'),
                        file_info.get('item_id'),
                    )
                )

        # then for the rest of the files, check if any chunks are already uploaded
        mhandler.SrvOutPutHandler.resume_check_in_progress()
        if len(unfinished_files) > 0:
            unfinished_items.extend(upload_client.resume_upload(unfinished_files))

    mhandler.SrvOutPutHandler.resume_warning(len(unfinished_items))
    mhandler.SrvOutPutHandler.resume_check_success()

    # lastly, start resumable upload for the rest of the chunks
    # thread number +1 reserve one thread to refresh token
    # and remove the token decorator in functions

    pool = ThreadPool(num_of_thread + 1)
    pool.apply_async(upload_client.upload_token_refresh)
    on_success_res = []
    for file_object in unfinished_items:
        chunk_res = upload_client.stream_upload(file_object, pool)
        # NOTE: if there is some racing error make the combine chunks
        # out of thread pool.
        res = pool.apply_async(
            upload_client.on_succeed,
            args=(file_object, manifest_json.get('tags'), chunk_res),
        )
        on_success_res.append(res)

    # finish the upload once all on success api return
    # otherwise wait for 1 second and check again
    [res.wait() for res in on_success_res]
    upload_client.set_finish_upload()

    pool.close()
    pool.join()

    num_of_file = len(unfinished_items)
    logger.info(f'Upload Time: {time.time() - upload_start_time:.2f}s for {num_of_file:d} files')
