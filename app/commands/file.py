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
import os.path
import re

import click
import questionary
import app.services.logger_services.log_functions as logger
import app.services.output_manager.help_page as file_help
import app.services.output_manager.message_handler as message_handler
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.services.file_manager.file_download import SrvFileDownload
from app.services.file_manager.file_list import SrvFileList
from app.services.file_manager.file_manifests import SrvFileManifests
from app.services.file_manager.file_tag import SrvFileTag
from app.services.file_manager.file_upload import assemble_path
from app.services.file_manager.file_upload import simple_upload
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.error_handler import customized_error_msg
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import doc
from app.utils.aggregated import fit_terminal_width
from app.utils.aggregated import get_zone
from app.utils.aggregated import identify_target_folder
from app.utils.aggregated import search_item
from app.utils.aggregated import void_validate_zone
from app.utils.aggregated import get_file_info_by_geid


@click.command()
def cli():
    """File Actions"""
    pass


@click.command(name="upload")
@click.argument("paths",
                type=click.Path(exists=True),
                nargs=-1)
@click.option('-p', '--project-path',
              help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_P))
@click.option('-a', '--attribute',
              default=None,
              required=False,
              help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_A),
              # type=click.Path(exists=True),
              show_default=True)
@click.option('-t', '--tag',
              default=None,
              required=False,
              multiple=True,
              help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_T),
              show_default=True)
@click.option('-z', '--zone',
              default=AppConfig.Env.green_zone,
              required=False,
              help=file_help.file_help_page(file_help.FileHELP.FILE_Z),
              show_default=True)
@click.option('-m', '--upload-message',
              default='',
              required=False,
              help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_M),
              show_default=True)
@click.option('-s', '--source-file',
              default=None,
              required=False,
              help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_S),
              show_default=True)
@click.option('--pipeline',
              default=None,
              required=False,
              help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_PIPELINE),
              show_default=True)
@click.option('--zip',
              default=None,
              required=False,
              is_flag=True,
              help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_ZIP),
              show_default=True)
@doc(file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD))
def file_put(**kwargs):
    paths = kwargs.get('paths')
    project_path = kwargs.get('project_path')
    tag = kwargs.get('tag')
    zone = kwargs.get('zone')
    upload_message = kwargs.get('upload_message')
    source_file = kwargs.get('source_file')
    pipeline = kwargs.get('pipeline')
    zipping = kwargs.get('zip')
    attribute = kwargs.get('attribute')

    user = UserConfig()
    # Check zone and upload-message
    zone = get_zone(zone) if zone else AppConfig.Env.green_zone.lower()
    void_validate_zone('upload', zone)
    toc = customized_error_msg(ECustomizedError.TOU_CONTENT).replace(' ', '...')
    if zone.lower() == AppConfig.Env.core_zone.lower() and click.confirm(fit_terminal_width(toc), abort=True):
        pass
    project_path = click.prompt('ProjectCode') if not project_path else project_path
    project_code, target_folder = identify_target_folder(project_path)
    srv_manifest = SrvFileManifests()
    upload_val_event = {
        "zone": zone, "upload_message": upload_message,
        "source": source_file, "process_pipeline": pipeline,
        "project_code": project_code, "token": user.access_token,
        "attribute": attribute, "tag": tag
    }
    validated_fieds = validate_upload_event(upload_val_event)
    src_file_info = validated_fieds['source_file']
    attribute = validated_fieds['attribute']
    if zone == AppConfig.Env.core_zone.lower():
        if not pipeline:
            # after validation, if not pipeline, provide default value
            pipeline = AppConfig.Env.pipeline_straight_upload
        else:
            if not bool(re.match(r"^[a-z0-9_-]{1,20}$", pipeline)):
                SrvErrorHandler.customized_handle(ECustomizedError.INVALID_PIPELINENAME, True)
        if not upload_message:
            upload_message = AppConfig.Env.default_upload_message
    # Unique Paths
    paths = set(paths)
    # upload files
    for f in paths:
        current_folder_node, result_file = assemble_path(f, target_folder, project_code, zone, user.access_token, zipping)
        upload_event = {
            'project_code': project_code,
            'file': f,
            'tags': tag if tag else [],
            'zone': zone,
            'upload_message': upload_message,
            'current_folder_node': current_folder_node,
            'compress_zip': zipping,
            'attribute': attribute
        }
        if pipeline:
            upload_event['process_pipeline'] = pipeline
        if source_file:
            upload_event['valid_source'] = src_file_info
        simple_upload(upload_event)
        srv_manifest.attach_manifest(attribute, result_file, zone) if attribute else None
        message_handler.SrvOutPutHandler.all_file_uploaded()


def validate_upload_event(event):
    """
    validate upload request, raise error when filed
    """
    app = AppConfig()
    zone = event.get('zone')
    upload_message = event.get('upload_message')
    source = event.get('source')
    process_pipeline = event.get('process_pipeline')
    project_code = event.get('project_code')
    token = event.get('token')
    attribute = event.get('attribute')
    tag = event.get('tag')
    source_file_info = {}
    if attribute:
        srv_manifest = SrvFileManifests()
        if not os.path.isfile(attribute):
            raise Exception('Attribute not exist in the given path')
        try:
            attribute = srv_manifest.read_manifest_template(attribute)
            attribute = srv_manifest.convert_import(attribute, project_code)
            srv_manifest.validate_manifest(attribute)
        except Exception:
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TEMPLATE, True)
    if tag:
        srv_tag = SrvFileTag()
        srv_tag.validate_taglist(tag)
    if zone == app.Env.core_zone.lower():
        if not upload_message:
            SrvErrorHandler.customized_handle(
                ECustomizedError.INVALID_UPLOAD_REQUEST, True, value="upload-message is required")
        if source:
            if not process_pipeline:
                SrvErrorHandler.customized_handle(
                    ECustomizedError.INVALID_UPLOAD_REQUEST,
                    True,
                    value="process pipeline name required"
                )
            else:
                source_file_info = search_item(project_code, zone, source, 'file', token)
                source_file_info = source_file_info['result']
                if not source_file_info:
                    SrvErrorHandler.customized_handle(ECustomizedError.INVALID_SOURCE_FILE, True, value=source)
    converted_content = {'source_file': source_file_info, 'attribute': attribute}
    return converted_content


@click.command(name="attribute-list")
@click.option(
    '-p', '--project-code',
    prompt='ProjectCode',
    help=file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_P))
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
@click.command(name="attribute-export")
@click.option(
    '-p', '--project-code',
    prompt='ProjectCode',
    help=file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_P))
@click.option(
    '-n', '--attribute-name',
    prompt='AttributeName',
    help=file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_N))
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


@click.command(name="list")
@click.argument("paths",
                type=click.STRING,
                nargs=1)
@click.option('-z', '--zone',
              default='greenroom',
              required=False,
              help=file_help.file_help_page(file_help.FileHELP.FILE_Z),
              show_default=True)
@click.option('--page',
              default=0,
              required=False,
              help=' The page to be listed',
              show_default=True)
@click.option('--page-size',
              default=10,
              required=False,
              help='number of objects per page',
              show_default=True)
@click.option('-d', '--detached',
              default=None,
              required=False,
              is_flag=True,
              help='whether run in detached mode',
              show_default=True)
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
        files = srv_list.list_files(paths, zone, page, page_size)
        query_result = fit_terminal_width(files)
        logger.info(query_result)
    else:
        while True:
            files = srv_list.list_files(paths, zone, page, page_size)
            if len(files) < page_size and page == 0:
                break
            elif len(files) < page_size and page != 0:
                choice = ['previous page', 'exit']
            elif page == 0:
                choice = ['next page', 'exit']
            else:
                choice = ['previous page', 'next page', 'exit']
            query_result = fit_terminal_width(files)
            logger.info(query_result)
            val = questionary.select(
                "\nWhat do you want?",
                qmark="",
                choices=choice).ask()
            if val == 'exit':
                # mhandler.SrvOutPutHandler.list_success('Project')
                break
            elif val == 'next page':
                click.clear()
                page += 1
            elif val == 'previous page':
                click.clear()
                page -= 1


@click.command(name="sync")
@click.argument("paths",
                type=click.STRING,
                nargs=-1)
@click.argument("output_path",
                type=click.Path(exists=True),
                nargs=1)
@click.option('-z', '--zone',
              default=AppConfig.Env.green_zone,
              required=False,
              help=file_help.file_help_page(file_help.FileHELP.FILE_SYNC_Z),
              show_default=False)
@click.option('--zip',
              default=None,
              required=False,
              is_flag=True,
              help=file_help.file_help_page(file_help.FileHELP.FILE_SYNC_ZIP),
              show_default=True)
@click.option('-i', '--geid',
              default=None,
              required=False,
              is_flag=True,
              help=file_help.file_help_page(file_help.FileHELP.FILE_SYNC_I),
              show_default=True)
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
    void_validate_zone('download', zone)
    user = UserConfig()
    if len(paths) == 0:
        SrvErrorHandler.customized_handle(ECustomizedError.MISSING_PROJECT_CODE, interactive)
    # Query file information and collecting errors
    if geid:
        item_res = get_file_info_by_geid(paths, user.access_token)
    else:
        item_res = []
        for path in paths:
            project_code = path.strip('/').split('/')[0]
            target_path = '/'.join(path.split('/')[1::])
            item = search_item(project_code, zone, target_path, '', user.access_token)
            if item.get('code') == 200 and item.get('result'):
                item_status = 'success'
                item_result = item.get('result')
                item_geid = item.get('result').get('id')
            elif item.get('code') == 403 and item.get('error_msg'):
                item_status = item.get('error_msg')
                item_result = {}
                item_geid = path
            else:
                item_status = 'File Not Exist'
                item_result = {}
                item_geid = path
            # when file not exist there will be no response, the geid will be input geid for error handling
            item_res.append({'status': item_status, 'result': item_result, 'geid': item_geid})
    # Downloading by batch or single
    if zipping and len(paths) > 1:
        srv_download = SrvFileDownload(interactive)
        srv_download.batch_download_file(output_path, item_res)
    else:
        for item in item_res:
            srv_download = SrvFileDownload(interactive)
            srv_download.simple_download_file(output_path, [item])
