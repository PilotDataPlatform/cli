import os.path
import click
from app.services.file_manager.file_upload import simple_upload, assemble_path
import app.services.logger_services.log_functions as logger
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler, customized_error_msg
from app.configs.user_config import UserConfig
from app.configs.app_config import AppConfig
from app.services.user_authentication.decorator import require_valid_token
from app.services.file_manager.file_manifests import SrvFileManifests
from app.services.file_manager.file_tag import SrvFileTag
from app.services.file_manager.file_list import SrvFileList
from app.services.file_manager.file_download import SrvFileDownload
from app.services.project_manager.aggregated import SrvProjectManager
import app.services.output_manager.message_handler as message_handler
from app.utils.aggregated import *
import app.services.output_manager.help_page as file_help


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
@click.option('-g', f'--{AppConfig.Env.dicom_project}-id',
              default=None,
              required=False,
              help=file_help.file_help_page(file_help.FileHELP.FILE_UPLOAD_G),
              show_default=True)
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
              default=None,
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
    dcm_id = kwargs.get(f'{AppConfig.Env.dicom_project}_id')
    tag = kwargs.get('tag')
    zone = kwargs.get('zone')
    upload_message = kwargs.get('upload_message')
    source_file = kwargs.get('source_file')
    pipeline = kwargs.get('pipeline')
    zip = kwargs.get('zip')
    attribute = kwargs.get('attribute')

    user = UserConfig()
    # Check zone and upload-message
    zone = get_zone(zone) if zone else AppConfig.Env.green_zone.lower()
    void_validate_zone('upload', zone, user.access_token)
    toc = customized_error_msg(ECustomizedError.TOU_CONTENT).replace(' ', '...')
    if zone.lower() == AppConfig.Env.core_zone.lower() and click.confirm(format_to_fit_terminal(toc), abort=True):
        pass
    interactive = True # add condition in situation no print needed
    if interactive:
        project_path = click.prompt('ProjectCode') if not project_path else project_path
        exiting_error = ''
    else:
        if project_path:
            exiting_error = ''
        else:
            project_path = ''
            exiting_error = 'Missing project code'
    if len(project_path.split('/')) > 1:
        target_folder = '/'.join(project_path.split('/')[1:])
        for f in target_folder.split('/'):
            f = f.strip(' ')
            valid = validate_folder_name(f)
            if not valid:
                SrvErrorHandler.customized_handle(ECustomizedError.INVALID_FOLDERNAME, True)
    else:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_NAMEFOLDER, True)
    srv_manifest = SrvFileManifests()
    if exiting_error:
        project_id = ''
        project_geid = ''
    else:
        project_code = project_path.split('/')[0]
        # Check project exist and get project_id
        project_id = SrvProjectManager(interactive).get_project_id_by_code(project_code)
        project_exist, project_geid = SrvProjectManager(interactive).get_project_geid_by_code(project_code)
        if not project_exist:
            exiting_error = project_geid
        
        if attribute:
            if not os.path.isfile(attribute):
                raise Exception('Attribute not exist in the given path')
            try:
                attribute = srv_manifest.read_manifest_template(attribute)
                attribute = srv_manifest.convert_import(attribute, project_code)
                srv_manifest.void_validate_manifest(attribute)
            except Exception as e:
                SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TEMPLATE, True)
        # validate tag
        if tag:
            srv_tag = SrvFileTag(interactive)
            valid_tag, result = srv_tag.validate_tag(tag, project_id)
            if not valid_tag:
                exiting_error = result

        upload_val_event = {"zone": zone, "upload_message": upload_message,
                            "source": source_file, "process_pipeline": pipeline,
                            "project_code": project_code, "token": user.access_token}
        void_upload_val(upload_val_event)
        if zone == AppConfig.Env.core_zone.lower():
            if not pipeline:
                # after validation, if not pipeline, provide default value
                pipeline = AppConfig.Env.pipeline_straight_upload
            if not upload_message:
                upload_message = AppConfig.Env.default_upload_message
        # validate pipeline name
        if pipeline:
            if not bool(re.match(r"^[a-z0-9_-]{1,20}$", pipeline)):
                SrvErrorHandler.customized_handle(
                    ECustomizedError.INVALID_PIPELINENAME, True)
    # Unique Paths
    paths = set(paths)
    # upload files
    for f in paths:
        current_folder_node, result_file = assemble_path(f, target_folder, project_code, zone, user.access_token, zip)
        upload_event = {"project_id": project_id,
                        'project_code': project_code,
                        'file': f,
                        'dcm_id': dcm_id if dcm_id else 'undefined',
                        'tags': tag if tag else [],
                        'zone': zone,
                        'upload_message': upload_message,
                        'current_folder_node': current_folder_node,
                        'compress_zip': zip,
                        "project_geid": project_geid}
        if pipeline:
            upload_event['process_pipeline'] = pipeline
        if source_file:
            upload_event['source_name'] = source_file
        simple_upload(upload_event)
        srv_manifest.attach_manifest(attribute, result_file, zone) if attribute else None
        message_handler.SrvOutPutHandler.all_file_uploaded()


@require_valid_token()
def void_upload_val(event):
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
    if zone == app.Env.core_zone.lower():
        if upload_message:
            pass
        else:
            SrvErrorHandler.customized_handle(
                ECustomizedError.INVALID_UPLOAD_REQUEST, True, value="upload-message is required")
        if source:
            if not process_pipeline:
                SrvErrorHandler.customized_handle(
                        ECustomizedError.INVALID_UPLOAD_REQUEST, True, value="process pipeline name required")
            else:
                _source_file_info = get_source_file(source, project_code, token)


@click.command(name="attribute-list")
@click.option('-p', '--project-code', prompt='ProjectCode', help=file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_P))
@require_valid_token()
@doc(file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_LIST))
def file_check_manifest(project_code):
    # check project exist
    srv_project = SrvProjectManager()
    _ = srv_project.get_project_geid_by_code(project_code)
    srv_manifest = SrvFileManifests(True)
    res = srv_manifest.list_manifest(project_code)
    if res.status_code == 200:
        manifest_list = res.json()['result']
        if manifest_list:
            message_handler.SrvOutPutHandler.print_manifest_table(manifest_list)
            message_handler.SrvOutPutHandler.all_manifest_fetched()
        else:
            message_handler.SrvOutPutHandler.project_has_no_manifest(project_code)
    else:
        error_message = res.text
        SrvErrorHandler.default_handle(error_message, True)


# to ignore unsupported option: context_settings=dict(ignore_unknown_options=True,  allow_extra_args=True,)
@click.command(name="attribute-export")
@click.option('-p', '--project-code', prompt='ProjectCode', help=file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_P))
@click.option('-n', '--attribute-name', prompt='AttributeName', help=file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_N))
@require_valid_token()
@doc(file_help.file_help_page(file_help.FileHELP.FILE_ATTRIBUTE_EXPORT))
def file_export_manifest(project_code, attribute_name):
    srv_project = SrvProjectManager()
    _project_exist = srv_project.get_project_geid_by_code(project_code)
    user = UserConfig()
    get_url = AppConfig.Connections.url_bff + "/v1/manifest/export"
    headers = {
        'Authorization': "Bearer " + user.access_token,
    }
    params = {'project_code': project_code,
              'manifest_name': attribute_name}
    res = requests.get(get_url, params=params, headers=headers)
    valid_res = res.json()
    srv_manifest = SrvFileManifests()
    if valid_res.get('code') == 200:
        manifests = valid_res['result']
        manifest_event = {'attributes': manifests.get('attributes'),
                          'manifest_name': attribute_name,
                          'project_code': project_code}
        res = srv_manifest.export_template(
            attribute_name, project_code, manifest_event)
        message_handler.SrvOutPutHandler.print_manifest_table(manifests)
        message_handler.SrvOutPutHandler.export_manifest_template(res[0])
        message_handler.SrvOutPutHandler.export_manifest_definition(res[1])
    else:
        result = valid_res.get('error_msg').split(' ')
        error_attr = '_'.join(result[:-1]).upper()
        validation_error = getattr(ECustomizedError, error_attr)
        SrvErrorHandler.customized_handle(validation_error, True, result[-1])


@click.command(name="list")
@click.argument("paths",
                type=click.STRING,
                nargs=1)
@click.option('-z', '--zone',
              default='greenroom',
              required=False,
              help=file_help.file_help_page(file_help.FileHELP.FILE_Z),
              show_default=True)
@require_valid_token()
@doc(file_help.file_help_page(file_help.FileHELP.FILE_LIST))
def file_list(paths, zone):
    zone = get_zone(zone) if zone else 'greenroom'
    if not zone:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_ZONE, True)
    if len(paths) == 0:
        SrvErrorHandler.customized_handle(
            ECustomizedError.MISSING_PROJECT_CODE, True)
    else:
        srv_project = SrvProjectManager()
        project_code = paths.strip('/').split('/')[0]
        _project_exist = srv_project.get_project_geid_by_code(project_code)
        srv_list = SrvFileList()
        files = srv_list.list_files(paths, zone)
        query_result = format_to_fit_terminal(files)
        logger.info(query_result)


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
def file_download(paths, output_path, zone, zip, geid):
    user = UserConfig()
    zone = get_zone(zone) if zone else AppConfig.Env.green_zone
    srv_project = SrvProjectManager()
    download_list = []
    if len(paths) > 1:
        interactive = False
    else:
        interactive = True
    if len(paths) == 0:
        SrvErrorHandler.customized_handle(ECustomizedError.MISSING_PROJECT_CODE, interactive)
    elif geid:
        for path in paths:
            if zip:
                download_list.append(path)
            else:
                srv_download = SrvFileDownload(path, zone, '', '', geid, interactive)
                srv_download.simple_download_file(output_path)
        if download_list:
            srv_download = SrvFileDownload(download_list, zone, '', '', geid, interactive)
            srv_download.batch_download_file(output_path)
    else:
        for path in paths:
            if len(path.split('/')) > 2:
                target_folder = '/'.join(path.split('/')[1:-1])
            else:
                target_folder = ''
            project_code = path.strip('/').split('/')[0]    
            project_geid = srv_project.get_project_geid_by_code(project_code)
            if target_folder:
                get_folder_in_project(project_code, zone, target_folder, user.access_token)
            if zip:
                download_list.append(path)
            else:
                srv_download = SrvFileDownload(path, zone, project_code, project_geid, by_geid=False, interactive=interactive)
                result = srv_download.simple_download_file(output_path)
                if not result:
                    continue
        if download_list:
            srv_download = SrvFileDownload(download_list, zone, project_code, project_geid, by_geid=False, interactive=interactive)
            srv_download.batch_download_file(output_path)
 