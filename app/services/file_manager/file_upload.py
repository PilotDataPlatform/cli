from app.models.service_meta_class import MetaService
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
import app.services.logger_services.log_functions as logger
import app.models.upload_form as uf
from app.services.user_authentication.decorator import require_valid_token
import os
import math
import click
import requests
import json
import uuid
import datetime
import sys
import zipfile
from app.utils.aggregated import *
import app.services.output_manager.error_handler as ehandler
from app.services.output_manager.error_handler import ECustomizedError, customized_error_msg
from app.services.project_manager.aggregated import SrvProjectManager
import time
from tqdm import tqdm
from app.configs.app_config import AppConfig
import app.services.output_manager.message_handler as mhandler
from .file_lineage import create_lineage
from ...utils.aggregated import get_file_in_folder


class SrvSingleFileUploader(metaclass=MetaService):
    def __init__(self,
                 file_path,
                 project_code,
                 container_id,
                 tags,
                 relative_path,
                 project_geid,
                 dcm_id='undefined',
                 zone=AppConfig.Env.green_zone,
                 upload_message="cli straight upload",
                 job_type='AS_FILE',
                 process_pipeline=None,
                 source_name=None,
                 current_folder_node='',
                 regular_file = True):
        self.user = UserConfig()
        self.user_info = get_user_info()
        self.operator = self.user_info['preferred_username']
        self.path = file_path
        self.upload_message = upload_message
        self.chunk_size = 1024 * 1024 * AppConfig.Env.chunk_size
        self.base_url = {
            AppConfig.Env.green_zone: AppConfig.Connections.url_upload_greenroom,
            AppConfig.Env.core_zone: AppConfig.Connections.url_upload_core
        }.get(zone.lower())
        self.zone = zone
        self.job_type = job_type
        self.project_code = project_code
        self.process_pipeline = process_pipeline
        self.source_name = source_name
        self.session_id = "cli-" + str(int(time.time()))
        self.upload_form = uf.FileUploadForm()
        self.upload_form.dcm_id = dcm_id
        self.upload_form.container_id = container_id
        self.upload_form.tags = tags
        self.upload_form.uploader = self.user.username
        self.upload_form.resumable_filename = [os.path.basename(self.path[0])] if job_type == 'AS_FILE' else self.path
        self.upload_form.resumable_relative_path = relative_path
        self.upload_form.current_folder_node = current_folder_node
        self.current_folder_node = current_folder_node
        self.project_geid = project_geid
        self.regular_file = regular_file

    def generate_meta(self):
        file_length_in_bytes = os.path.getsize(self.path)
        self.upload_form.resumable_total_size = file_length_in_bytes
        self.upload_form.resumable_total_chunks = math.ceil(
            self.upload_form.resumable_total_size / self.chunk_size)
        mhandler.SrvOutPutHandler.uploading_files(self.upload_form.uploader,
                                                  self.project_code,
                                                  self.upload_form.resumable_total_size,
                                                  self.upload_form.resumable_total_chunks,
                                                  self.upload_form.resumable_relative_path.strip('/'))
        return self.upload_form.to_dict

    @require_valid_token()
    def pre_upload(self):
        url = AppConfig.Connections.url_bff + "/v1/project/{}/files".format(self.project_code) \
            if self.zone == AppConfig.Env.core_zone else self.base_url + "/v1/files/jobs"
        file_type = "processed" if self.zone == AppConfig.Env.core_zone else "raw"
        payload = uf.generate_pre_upload_form(
            self.project_code,
            self.operator,
            self.upload_form,
            zone=self.zone,
            upload_message=self.upload_message,
            job_type=self.job_type,
            file_type=file_type,
            current_folder_node=self.current_folder_node)
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
            'Session-ID': self.session_id
        }
        response = resilient_session().post(url, json=payload, headers=headers)
        if response.status_code == 200:
            res_to_dict = response.json()
            result = res_to_dict.get("result")
            res = {}
            for job in result:
                relative_path = job.get('source')
                resumable_id = job.get('payload').get('resumable_identifier')
                res[relative_path] = resumable_id
            mhandler.SrvOutPutHandler.preupload_success()
            return res
        elif response.status_code == 403:
            res_to_dict = response.json()
            ehandler.SrvErrorHandler.customized_handle(
                ehandler.ECustomizedError.PERMISSION_DENIED, self.regular_file)
        elif response.status_code == 401:
            ehandler.SrvErrorHandler.customized_handle(
                ehandler.ECustomizedError.PROJECT_DENIED, self.regular_file)
        elif response.status_code == 409:
            ehandler.SrvErrorHandler.customized_handle(
                ehandler.ECustomizedError.FILE_EXIST, self.regular_file)
            raise Exception('file exist')
        elif response.status_code == 400 and 'Invalid operation, locked' in response.json().get('error_msg'):
            ehandler.SrvErrorHandler.customized_handle(ehandler.ECustomizedError.FILE_LOCKED, True)
        elif response.status_code == 500 and 'Invalid operation, locked' in response.json().get('error_msg'):
            ehandler.SrvErrorHandler.customized_handle(ehandler.ECustomizedError.FILE_LOCKED, True)
        else:
            ehandler.SrvErrorHandler.default_handle(
                str(response.status_code) + ": " + str(response.content), self.regular_file)

    def stream_upload(self):
        count = 0
        remaining_size = self.upload_form.resumable_total_size
        with tqdm(
            total=self.upload_form.resumable_total_size,
            leave=True,
            bar_format="{desc} |{bar:30} {percentage:3.0f}% {remaining}"
            ) as bar:
            bar.set_description('Uploading {}'.format(self.upload_form.resumable_filename))
            f = open(self.path, 'rb')
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                else:
                    self.upload_chunk(count + 1, chunk)
                    if self.chunk_size > remaining_size:
                        bar.update(remaining_size)
                    else:
                        bar.update(self.chunk_size)
                    count += 1  # uploaded successfully
                    remaining_size = remaining_size - self.chunk_size
            f.close()


    @require_valid_token()
    def upload_chunk(self, chunk_number, chunk):
        url = self.base_url + "/v1/files/chunks"
        payload = uf.generate_chunk_form(
            self.project_code,
            self.operator,
            self.upload_form,
            chunk_number)
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
            'Session-ID': self.session_id
        }
        files = {
            'chunk_data': chunk,
        }
        # retry three times
        for i in range(AppConfig.Env.resilient_retry):
            response = resilient_session().post(
                url, data=payload, headers=headers, files=files)
            if response.status_code == 200:
                res_to_dict = response.json()
                return res_to_dict
            else:
                if i == 2:
                    print("retry failed, code: " + str(response.status_code))
                    ehandler.SrvErrorHandler.default_handle(
                        response.content, True)

    @require_valid_token()
    def on_succeed(self):
        url = self.base_url + "/v1/files"
        payload = uf.generate_on_success_form(
            self.project_code, self.operator, self.upload_form,
            [],
            process_pipeline=self.process_pipeline,
            upload_message=self.upload_message)
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
            'Refresh-token': self.user.refresh_token,
            'Session-ID': self.session_id
        }
        response = resilient_session().post(url, json=payload, headers=headers)
        if response.status_code == 200:
            res_to_dict = response.json()
            mhandler.SrvOutPutHandler.start_finalizing()
            return res_to_dict['result']['job_id']
        else:
            ehandler.SrvErrorHandler.default_handle(response.content, True)

    @require_valid_token()
    def create_file_lineage(self):
        if self.source_name and self.zone == AppConfig.Env.core_zone:
            if self.upload_form.dcm_id != 'undefined':
                child_rel_path = self.upload_form.resumable_relative_path + self.upload_form.dcm_id + '_' + self.upload_form.resumable_filename
            else:
                child_rel_path = self.upload_form.resumable_relative_path + self.upload_form.resumable_filename
            child_file = get_source_file(child_rel_path, self.project_code,
                                         self.user.access_token)
            parent_file = get_source_file(self.source_name, self.project_code,
                                          self.user.access_token)
            child_file_geid = child_file[0]['global_entity_id']
            parent_file_geid = parent_file[0]['global_entity_id']
            create_lineage(child_file_geid, parent_file_geid, self.user.access_token,
                           self.project_code, self.process_pipeline, self.operator)

    @require_valid_token()
    def check_status(self):
        url = self.base_url + "/v1/files/jobs"
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
            'Session-ID': self.session_id
        }
        query = {
            'project_code': self.project_code,
            'operator': self.operator}
        response = requests.get(url, headers=headers, params=query)
        sys.stdout.write("\033[F")
        mhandler.SrvOutPutHandler.finalize_upload()
        if response.status_code == 200:
            res_to_dict = response.json()['result']
            task_found = [task for task in res_to_dict if task['job_id']
                          == self.upload_form.resumable_identifier][0]
            is_done = task_found['status'] == 'SUCCEED'
            is_terminated = task_found['status'] == 'TERMINATED'
            if is_done:
                mhandler.SrvOutPutHandler.upload_job_done()
            if is_terminated:
                ehandler.SrvErrorHandler.default_handle(
                    'Upload Terminated: {}'.format(response.text), True)
            return is_done
        elif response.status_code == 404:
            return False
        else:
            ehandler.SrvErrorHandler.default_handle(response.content)

    @require_valid_token()
    def void_check_genetate_id(self, my_id):
        if not my_id:
            ehandler.SrvErrorHandler.customized_handle(
                ehandler.ECustomizedError.DICOM_ID_NOT_FOUND,
                True)
        validate_url = AppConfig.Connections.url_bff + "/v1/validate/gid"
        payload = {'dcm_id': my_id}
        headers = {'Authorization': "Bearer " + self.user.access_token}
        validation_result = requests.post(validate_url,
                                          headers=headers,
                                          json=payload)
        if validation_result.json():
            code = validation_result.json().get('code')
            result = validation_result.json().get('result')
        else:
            code = 500
            result = 'Failed to validate'
        if result != 'Valid' or code != 200:
            ehandler.SrvErrorHandler.customized_handle(
                ehandler.ECustomizedError.INVALID_DICOM_ID,
                True)


def compress_folder_to_zip(path):
    path = path.rstrip('/').lstrip()
    zipfile_path = path + '.zip'
    mhandler.SrvOutPutHandler.start_zipping_file()
    zipf = zipfile.ZipFile(zipfile_path, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for file in files:
            zipf.write(os.path.join(root, file))
    zipf.close()


def convert_filename(path, base_name, job_type, dcm_id, target_folder):
    file_name = os.path.basename(path)
    relative_file_path = os.path.relpath(path)
    if dcm_id != 'undefined' and dcm_id:
        if target_folder == '':
            converted_filename = dcm_id + '_' + file_name
        else:
            converted_filename = target_folder + '/' + dcm_id + '_' + file_name
        _relative_path = ''
    elif job_type == 'AS_FILE':
        if target_folder == '':
            converted_filename = file_name
        else:
            converted_filename = target_folder + '/' + file_name
        _relative_path = ''
    else:
        converted_filename = relative_file_path[relative_file_path.index(base_name):]
        _relative_path = relative_file_path[relative_file_path.index(base_name):(relative_file_path.rindex(file_name)-1)]
        if target_folder == '':
            pass
        else:
            converted_filename = target_folder + '/' + '/'.join(converted_filename.split('/')[1:])
    return converted_filename, _relative_path


def assemble_path(f, target_folder, project_code, zone, access_token, zip=False):
    # if os.path.basename(f.rstrip('/')).lower() in ['raw', 'logs', 'workdir', 'trash', 'log']:
    #     ehandler.SrvErrorHandler.customized_handle(ECustomizedError.RESERVED_FOLDER, True)
    if target_folder == '':
        current_folder_node = target_folder
        result_file = os.path.basename(f)
    else:
        current_folder_node = target_folder + '/' + f.rstrip('/').split('/')[-1]
        result_file = current_folder_node
        name_folder = current_folder_node.split('/')[0].lower()
        name_folder_res = get_folder_in_project(project_code, zone, name_folder, access_token)
        res = get_folder_in_project(project_code, zone, target_folder, access_token)
        # if current_folder_node.split('/')[0].lower() in ['raw', 'logs', 'workdir', 'trash', 'log']:
        #     ehandler.SrvErrorHandler.customized_handle(ECustomizedError.RESERVED_FOLDER, True)
        if not name_folder_res:
            ehandler.SrvErrorHandler.customized_handle(ECustomizedError.INVALID_NAMEFOLDER, True)
        elif not res and project_code != AppConfig.Env.dicom_project:
            click.confirm(customized_error_msg(ECustomizedError.CREATE_FOLDER_IF_NOT_EXIST), abort=True)
        elif not res and project_code == AppConfig.Env.dicom_project:
            ehandler.SrvErrorHandler.customized_handle(ECustomizedError.UNSUPPORTED_PROJECT, True, value=': Folder not exist')
        else:
            pass
    if zip:
        result_file = result_file + '.zip'
    return current_folder_node, result_file


def simple_upload(upload_event):
    my_file = upload_event.get('file')
    project_id = upload_event.get('project_id')
    project_code = upload_event.get('project_code')
    dcm_id = upload_event.get('dcm_id')
    tags = upload_event.get('tags')
    zone = upload_event.get('zone')
    source_name = upload_event.get('source_name')
    process_pipeline = upload_event.get('process_pipeline', None)
    upload_message = upload_event.get('upload_message', 'cli straight upload')
    target_folder = upload_event.get('current_folder_node', '')
    compress_zip = upload_event.get('compress_zip', False)
    project_geid = upload_event.get('project_geid')
    regular_file = upload_event.get('regular_file', True)
    mhandler.SrvOutPutHandler.start_uploading(my_file)
    base_path = ''
    if os.path.isdir(my_file):
        job_type = 'AS_FILE' if compress_zip else 'AS_FOLDER'
        if job_type == 'AS_FILE':
            upload_file_path = [my_file.rstrip('/').lstrip() + '.zip']
            target_folder = '/'.join(target_folder.split('/')[:-1]).rstrip('/')
            compress_folder_to_zip(my_file)
        else:
            logger.warn("Current version does not support folder tagging, "
                        "any selected tags will be ignored")
            upload_file_path = get_file_in_folder(my_file)
            base_path = my_file.rstrip('/').split('/')[-1]
    else:
        job_type = 'AS_FILE'
        upload_file_path = [my_file]
        target_folder = '/'.join(target_folder.split('/')[:-1]).rstrip('/')
    file_uploader = SrvSingleFileUploader(
        file_path=upload_file_path,
        project_code=project_code,
        container_id=project_id,
        dcm_id=dcm_id,
        tags=tags,
        zone=zone,
        job_type=job_type,
        upload_message=upload_message,
        process_pipeline=process_pipeline,
        source_name=source_name,
        relative_path=base_path,
        current_folder_node=target_folder,
        project_geid=project_geid,
        regular_file=regular_file)
    if project_code == AppConfig.Env.dicom_project:
        file_uploader.void_check_genetate_id(dcm_id)
        if job_type =='AS_FOLDER':
            ehandler.SrvErrorHandler.customized_handle(ehandler.ECustomizedError.UNSUPPORTED_PROJECT,
                                                       True, value=': Upload folder')
    # file_uploader.validate_upload_action()
    file_identities = file_uploader.pre_upload()
    for path in upload_file_path:
        file_uploader.path = path
        file_uploader.upload_form.resumable_filename = os.path.basename(path)
        converted_filename, rel_path = convert_filename(path, base_path, job_type,
                                                        file_uploader.upload_form.dcm_id, target_folder)
        if target_folder == "":
            file_uploader.upload_form.resumable_relative_path = rel_path
        else:
            file_uploader.upload_form.resumable_relative_path = target_folder + '/' \
                                                                + '/'.join(rel_path.split('/')[1:])
        file_uploader.upload_form.resumable_identifier = file_identities.get(converted_filename)
        file_uploader.generate_meta()
        file_uploader.stream_upload()
        res_on_succeed = file_uploader.on_succeed()
    continue_loop = True
    while continue_loop:
        succeed = file_uploader.check_status()
        continue_loop = not succeed
        time.sleep(0.5)
    file_uploader.create_file_lineage()
    os.remove(upload_file_path[0]) if os.path.isdir(my_file) and job_type == 'AS_FILE' else None
    return res_on_succeed
