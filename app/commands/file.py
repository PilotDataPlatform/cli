# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import json
import os
from sys import exit

import click
from click.exceptions import Abort

import app.services.output_manager.help_page as file_help
import app.services.output_manager.message_handler as message_handler
from app.configs.app_config import AppConfig
from app.models.item import ItemStatus
from app.models.item import ItemType
from app.services.file_manager.file_download.download_client import SrvFileDownload
from app.services.file_manager.file_list import SrvFileList
from app.services.file_manager.file_manifests import SrvFileManifests
from app.services.file_manager.file_metadata.file_metadata_client import FileMetaClient
from app.services.file_manager.file_move.file_move_client import FileMoveClient
from app.services.file_manager.file_trash.file_trash_client import FileTrashClient
from app.services.file_manager.file_trash.utils import parse_trash_paths
from app.services.file_manager.file_upload.file_upload import assemble_path
from app.services.file_manager.file_upload.file_upload import resume_upload
from app.services.file_manager.file_upload.file_upload import simple_upload
from app.services.file_manager.file_upload.upload_validator import UploadEventValidator
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.error_handler import customized_error_msg
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import doc
from app.utils.aggregated import fit_terminal_width
from app.utils.aggregated import get_file_info_by_geid
from app.utils.aggregated import get_zone
from app.utils.aggregated import identify_target_folder
from app.utils.aggregated import normalize_input_paths
from app.utils.aggregated import normalize_join
from app.utils.aggregated import remove_the_output_file
from app.utils.aggregated import search_item


@click.command()
def cli():
    """File Actions."""
    pass


@click.command(name='upload')
@click.argument('object_path', type=str)
@click.argument('files', type=click.Path(exists=True), nargs=-1)
@click.option(
    '-a',
    '--attribute',
    default=None,
    required=False,
    help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_A),
    type=click.File('rb'),
    show_default=True,
)
@click.option(
    '-t',
    '--tag',
    default=None,
    required=False,
    multiple=True,
    help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_T),
    type=click.File('rb'),
    show_default=True,
)
@click.option(
    '-z',
    '--zone',
    default=AppConfig.Env.green_zone,
    required=False,
    help=file_help.file_help_page(file_help.FileHELP.FILE_Z),
    show_default=True,
)
@click.option(
    '-s',
    '--source-file',
    default=None,
    required=False,
    help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_S),
    show_default=True,
)
@click.option(
    '--zip',
    default=None,
    required=False,
    is_flag=True,
    help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_ZIP),
    show_default=True,
)
@click.option(
    '--thread',
    '-td',
    default=1,
    required=False,
    help='The number of threads for uploading a file.',
    show_default=True,
)
@click.option(
    '--output-path',
    '-o',
    default='./resumable_upload_log.json',
    required=False,
    help='The output path for the manifest file of resumable upload log.',
    show_default=True,
)
@doc(file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD))
@normalize_input_paths(['files'])
def file_put(**kwargs):  # noqa: C901
    """"""

    project_path = kwargs.get('object_path').strip('/')
    files = kwargs.get('files')

    tag_files = kwargs.get('tag')
    zone = kwargs.get('zone')
    source_file = kwargs.get('source_file')
    zipping = kwargs.get('zip')
    attribute_file = kwargs.get('attribute')
    thread = kwargs.get('thread')
    output_path = kwargs.get('output_path')

    # load tag json file to list, and attribute file to dict
    try:
        tag = []
        for t_f in tag_files:
            tag.extend(json.load(t_f))
    except Exception:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TAG_FILE, True)
    try:
        attribute = json.load(attribute_file) if attribute_file else None
    except Exception:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TEMPLATE, True)

    # Check zone and upload-message
    zone = get_zone(zone) if zone else AppConfig.Env.green_zone.lower()
    toc = customized_error_msg(ECustomizedError.TOU_CONTENT).replace(' ', '...')
    try:
        if zone.lower() == AppConfig.Env.core_zone.lower() and click.confirm(fit_terminal_width(toc), abort=True):
            pass
    except Abort:
        message_handler.SrvOutPutHandler.cancel_upload()
        exit(1)

    # check if user input at least one file/folder
    if len(files) == 0:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_PATHS, True)

    # check if the manifest file exists
    try:
        if os.path.exists(output_path):
            click.confirm(
                customized_error_msg(ECustomizedError.MANIFEST_OF_FOLDER_FILE_EXIST) % (output_path), abort=True
            )
    except Abort:
        message_handler.SrvOutPutHandler.cancel_upload()
        exit(1)

    project_code, folder_type, target_folder = identify_target_folder(project_path)
    srv_manifest = SrvFileManifests()
    upload_val_event = {
        'zone': zone,
        'source': source_file,
        'project_code': project_code,
        'attribute': attribute,
        'tag': tag,
    }
    validated_fieds = validate_upload_event(upload_val_event)
    src_file_info = validated_fieds['source_file']
    attribute = validated_fieds['attribute']

    # for the path formating there will be following cases:
    # - file:
    #   1. the project path exist, then will be AS_FILE. nothing will be changed.
    #      current_folder_node will be empty string.
    #   2. the project path not exist, then will be AS_FOLDER. the current_folder_node will
    #      be the parent folder node + the shortest non-exist folder. (like one level down).
    # - folder:
    #   1. the project path exist, then will be AS_FOLDER. the current folder node will be
    #      the one that user input.
    #   2. the project path not exist, then will be AS_FOLDER. the current folder node will
    #      be the parent folder node + the shortest non-exist folder. (like one level down).

    # Unique Paths
    files = set(files)
    # the loop will read all input path(folder or files)
    # and process them one by one
    for f in files:
        # so this function will always return the furthest folder node as current_folder_node+parent_folder_id
        current_folder_node, parent_folder, create_folder_flag, target_folder = assemble_path(
            f,
            target_folder,
            project_code,
            folder_type,
            zone,
        )

        upload_event = {
            'project_code': project_code,
            'target_folder': target_folder,
            'file': f.rstrip('/'),  # remove the ending slash
            'tags': tag if tag else [],
            'zone': zone,
            'current_folder_node': current_folder_node,
            'parent_folder_id': parent_folder.get('id'),
            'create_folder_flag': create_folder_flag,
            'compress_zip': zipping,
            'attribute': attribute,
        }
        if source_file:
            upload_event['source_id'] = src_file_info.get('id', '')

        item_ids = simple_upload(upload_event, num_of_thread=thread, output_path=output_path)

        # since only file upload can attach manifest, take the first file object
        srv_manifest.attach_manifest(attribute, item_ids[0], zone) if attribute else None
        message_handler.SrvOutPutHandler.all_file_uploaded()

        remove_the_output_file(output_path)


@click.command(name='resume')
@click.option(
    '--thread',
    '-td',
    default=1,
    required=False,
    help='The number of thread for upload a file',
    show_default=True,
)
@click.option(
    '--resumable-manifest',
    '-r',
    default=None,
    required=True,
    help='The resumable upload log file',
    show_default=True,
)
@doc(file_help.file_help_page(file_help.FileHELP.FILE_RESUME))
def file_resume(**kwargs):  # noqa: C901
    """
    Summary:
        Resume upload file. Now split the logic of resumable upload and
        normal file upload to make the code more clear.
    Parameters:
        - thread: The number of thread for upload a file
        - resumable_file: The manifest file for resumable upload
    """

    thread = kwargs.get('thread')
    resumable_manifest_file = kwargs.get('resumable_manifest')

    # check if manifest file exist then read the manifest file as json
    if not os.path.exists(resumable_manifest_file):
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_RESUMABLE, True)

    with open(resumable_manifest_file, 'r') as f:
        resumable_manifest = json.load(f)
        # use the same validator with upload. because resumable and normal upload
        # are rather similar with the input
        validate_upload_event(resumable_manifest)

    resume_upload(resumable_manifest, thread)

    # since only file upload can attach manifest, take the first file object
    srv_manifest = SrvFileManifests()
    item_id = next(iter(resumable_manifest.get('file_objects')))
    attribute = resumable_manifest.get('attributes')
    zone = resumable_manifest.get('zone')
    srv_manifest.attach_manifest(attribute, item_id, zone) if attribute else None
    message_handler.SrvOutPutHandler.all_file_uploaded()

    remove_the_output_file(resumable_manifest_file)


def validate_upload_event(event):
    """validate upload request, raise error when filed."""
    zone = event.get('zone')
    source = event.get('source')
    project_code = event.get('project_code')
    attribute = event.get('attribute')
    tag = event.get('tag')
    validator = UploadEventValidator(project_code, zone, source, attribute, tag)
    converted_content = validator.validate_upload_event()
    return converted_content


@click.command(name='attribute-list')
@click.option(
    '-p', '--project-code', prompt='ProjectCode', help=file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_P)
)
@require_valid_token()
@doc(file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_LIST))
def file_check_manifest(project_code):
    srv_manifest = SrvFileManifests(True)
    res = srv_manifest.list_manifest(project_code)
    res_json = res.json()
    if res_json.get('code') == 200:
        manifest_list = res_json['result']
        if manifest_list:
            message_handler.SrvOutPutHandler.print_manifest_table(manifest_list)
            message_handler.SrvOutPutHandler.all_manifest_fetched()
        else:
            message_handler.SrvOutPutHandler.project_has_no_manifest(project_code)
    else:
        message_handler.SrvOutPutHandler.project_has_no_manifest(project_code)


# to ignore unsupported option: context_settings=dict(ignore_unknown_options=True,  allow_extra_args=True,)
@click.command(name='attribute-export')
@click.option(
    '-p', '--project-code', prompt='ProjectCode', help=file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_P)
)
@click.option(
    '-n', '--attribute-name', prompt='AttributeName', help=file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_N)
)
@require_valid_token()
@doc(file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_EXPORT))
def file_export_manifest(project_code, attribute_name):
    srv_manifest = SrvFileManifests(True)
    manifest_info = srv_manifest.export_manifest(project_code, attribute_name)
    if manifest_info:
        res = srv_manifest.export_template(project_code, manifest_info[0])
        message_handler.SrvOutPutHandler.print_manifest_table(manifest_info)
        message_handler.SrvOutPutHandler.export_manifest_template(res[0])
        message_handler.SrvOutPutHandler.export_manifest_definition(res[1])
    else:
        message_handler.SrvOutPutHandler.project_has_no_manifest(project_code)


@click.command(name='list')
@click.argument('paths', type=click.STRING, nargs=1)
@click.option(
    '-z',
    '--zone',
    default='greenroom',
    required=False,
    help=file_help.file_help_page(file_help.FileHELP.FILE_Z),
    show_default=True,
)
@click.option('--page', default=0, required=False, help=' The page to be listed', show_default=True)
@click.option('--page-size', default=10, required=False, help='number of objects per page', show_default=True)
@click.option(
    '-d',
    '--detached',
    default=None,
    required=False,
    is_flag=True,
    help='whether run in detached mode',
    show_default=True,
)
@require_valid_token()
@doc(file_help.file_help_page(file_help.FileHELP.FILE_LIST))
def file_list(paths, zone, page, page_size, detached):
    zone = get_zone(zone) if zone else 'greenroom'
    if not zone:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_ZONE, True)
    if len(paths) == 0:
        SrvErrorHandler.customized_handle(ECustomizedError.MISSING_PROJECT_CODE, True)

    srv_list = SrvFileList()
    if detached:
        srv_list.list_files_without_pagination(paths, zone, page, page_size)
    else:
        srv_list.list_files_with_pagination(paths, zone, page, page_size)


@click.command(name='download')
@click.argument('paths', type=click.STRING, nargs=-1)
@click.argument('output_path', type=click.Path(exists=True), nargs=1)
@click.option(
    '-z',
    '--zone',
    default=AppConfig.Env.green_zone,
    required=False,
    help=file_help.file_help_page(file_help.FileHELP.FILE_SYNC_Z),
    show_default=False,
)
@click.option(
    '--zip',
    default=None,
    required=False,
    is_flag=True,
    help=file_help.file_help_page(file_help.FileHELP.FILE_SYNC_ZIP),
    show_default=True,
)
@click.option(
    '-i',
    '--geid',
    default=None,
    required=False,
    is_flag=True,
    help=file_help.file_help_page(file_help.FileHELP.FILE_SYNC_I),
    show_default=True,
)
@require_valid_token()
@doc(file_help.file_help_page(file_help.FileHELP.FILE_SYNC))
def file_download(**kwargs):
    paths = kwargs.get('paths')
    output_path = kwargs.get('output_path')
    zone = kwargs.get('zone')
    zipping = kwargs.get('zip')
    geid = kwargs.get('geid')
    zone = get_zone(zone) if zone else AppConfig.Env.green_zone
    interactive = False if len(paths) > 1 else True
    # void_validate_zone('download', zone)

    if len(paths) == 0:
        SrvErrorHandler.customized_handle(ECustomizedError.MISSING_PROJECT_CODE, interactive)
    # Query file information and collecting errors
    if geid:
        item_res = get_file_info_by_geid(paths)
    else:
        item_res = []
        for path in paths:
            project_code, root_folder, object_path = path.strip('/').split('/', 2)
            root_type = ItemType.get_type_from_keyword(root_folder)
            object_path = normalize_join(root_type.get_prefix_by_type(), object_path)

            # search the target item and download to local
            item = search_item(project_code, zone, object_path)
            if item.get('code') == 200 and item.get('result'):
                item_status = 'success'
                item_result = item.get('result')
                item_geid = item.get('result').get('id')
            else:
                item_status = 'File Not Exist'
                item_result = {}
                item_geid = path
            # when file not exist there will be no response, the geid will be input geid for error handling
            item_res.append({'status': item_status, 'result': item_result, 'geid': item_geid})

    # Downloading by batch or single
    if zipping and len(paths) > 1:
        srv_download = SrvFileDownload(zone, interactive)
        srv_download.batch_download_file(output_path, item_res)
    else:
        for item in item_res:
            srv_download = SrvFileDownload(zone, interactive)
            srv_download.simple_download_file(output_path, [item])


@click.command(name='metadata')
@click.argument('file_path', type=click.STRING)
@click.option(
    '-z',
    '--zone',
    default=AppConfig.Env.green_zone,
    required=True,
    help=file_help.file_help_page(file_help.FileHELP.FILE_META_Z),
    show_default=False,
)
@click.option(
    '-g',
    '--general',
    default=None,
    required=True,
    help=file_help.file_help_page(file_help.FileHELP.FILE_META_G),
    show_default=True,
)
@click.option(
    '-a',
    '--attribute',
    default=None,
    required=True,
    help=file_help.file_help_page(file_help.FileHELP.FILE_META_A),
    show_default=True,
)
@click.option(
    '-t',
    '--tag',
    default=None,
    required=True,
    help=file_help.file_help_page(file_help.FileHELP.FILE_META_T),
    show_default=True,
)
@require_valid_token()
@doc(file_help.file_help_page(file_help.FileHELP.FILE_META))
def file_metadata_download(**kwargs):
    '''
    Summary:
        Download metadata of a file including general, attribute and tag.
    '''

    file_path = kwargs.get('file_path')
    zone = kwargs.get('zone')
    general_folder = kwargs.get('general').rstrip('/')
    attribute_folder = kwargs.get('attribute').rstrip('/')
    tag_folder = kwargs.get('tag').rstrip('/')

    # Check zone and upload-message
    zone = get_zone(zone) if zone else AppConfig.Env.green_zone.lower()
    file_meta_client = FileMetaClient(zone, file_path, general_folder, attribute_folder, tag_folder)
    file_meta_client.download_file_metadata()

    message_handler.SrvOutPutHandler.metadata_download_success()


@click.command(name='move')
@click.argument('src_item_path', type=click.STRING)
@click.argument('dest_item_path', type=click.STRING)
@click.option(
    '-z',
    '--zone',
    default=AppConfig.Env.green_zone,
    required=True,
    help=file_help.file_help_page(file_help.FileHELP.FILE_MOVE_Z),
    show_default=False,
)
@require_valid_token()
@doc(file_help.file_help_page(file_help.FileHELP.FILE_MOVE))
def file_move(**kwargs):
    # src_item_path and dest_item_path are composed of project_code and folder_name
    src_item_path = kwargs.get('src_item_path').strip('/')
    dest_item_path = kwargs.get('dest_item_path').strip('/')
    zone = kwargs.get('zone')

    src_project_code, src_item = src_item_path.split('/', 1)
    dest_project_code, dest_item = dest_item_path.split('/', 1)
    if src_project_code != dest_project_code:
        message_handler.SrvOutPutHandler.move_action_failed(
            src_item_path, dest_item_path, 'Cannot move files between different projects'
        )
        exit(1)
    elif len(src_item.split('/')) <= 2 or len(dest_item.split('/')) <= 1:
        message_handler.SrvOutPutHandler.move_action_failed(
            src_item_path, dest_item_path, 'Cannot move root/name/shared folders'
        )
        exit(1)

    # tranlate keyword to correct object path
    src_keyword, src_path = src_item.split('/', 1)
    dest_keyword, dest_path = dest_item.split('/', 1)

    src_type = ItemType.get_type_from_keyword(src_keyword)
    dest_type = ItemType.get_type_from_keyword(dest_keyword)

    src_path = src_type.get_prefix_by_type() + src_path
    dest_path = dest_type.get_prefix_by_type() + dest_path

    zone = get_zone(zone) if zone else AppConfig.Env.green_zone.lower()
    file_meta_client = FileMoveClient(zone, src_project_code, src_path, dest_path)
    file_meta_client.move_file()

    message_handler.SrvOutPutHandler.move_action_success(src_item_path, dest_item_path)


@click.command(name='trash')
@click.argument('paths', type=click.STRING, nargs=-1)
@click.option(
    '-z',
    '--zone',
    required=True,
    type=click.STRING,
    help=file_help.file_help_page(file_help.FileHELP.FILE_Z),
)
@click.option(
    '--permanent',
    default=False,
    required=False,
    is_flag=True,
    help=file_help.file_help_page(file_help.FileHELP.FILE_TRASH_P),
)
@doc(file_help.file_help_page(file_help.FileHELP.FILE_TRASH))
def file_trash(paths: str, zone: str, permanent: bool):
    # group path by parent folder
    project_code, items = parse_trash_paths(paths, zone, permanent)

    for parent_id, item_ids in items.items():
        root_folder, item_ids = item_ids['root_folder'], item_ids['items']
        trash_client = FileTrashClient(project_code, parent_id, item_ids, zone)

        # only when item status is active or root is not trash bin
        if root_folder != ItemType.TRASH:
            trash_client.move_to_trash()
            failed_item = trash_client.check_status(ItemStatus.TRASHED)
            if failed_item:
                SrvErrorHandler.customized_handle(ECustomizedError.TRASH_FAIL, True, failed_item)

        # if permanent flag is set, then permanently delete the files
        if permanent:
            trash_client.permanently_delete()
            failed_item = trash_client.check_status(ItemStatus.DELETED)
            if failed_item:
                SrvErrorHandler.customized_handle(ECustomizedError.DELETE_FAIL, True, failed_item)

    message_handler.SrvOutPutHandler.trash_delete_success(list(paths), permanent)
