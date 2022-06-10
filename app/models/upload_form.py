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

import os

from app.configs.app_config import AppConfig


class FileUploadForm:
    def __init__(self):
        self._attribute_map = {
            "resumable_identifier": "",
            "resumable_filename": "",
            "resumable_chunk_number": -1,
            "resumable_total_chunks": -1,
            "resumable_total_size": -1,
            "resumable_relative_path": "",
            "tags": [],
            "uploader": "",
            "metadatas": None,
            "container_id": "",
        }

    @property
    def to_dict(self):
        return self._attribute_map

    @property
    def resumable_identifier(self):
        return self._attribute_map['resumable_identifier']

    @resumable_identifier.setter
    def resumable_identifier(self, resumable_identifier):
        self._attribute_map['resumable_identifier'] = resumable_identifier

    @property
    def resumable_filename(self):
        return self._attribute_map['resumable_filename']

    @resumable_filename.setter
    def resumable_filename(self, resumable_filename):
        self._attribute_map['resumable_filename'] = resumable_filename

    @property
    def resumable_chunk_number(self):
        return self._attribute_map['resumable_chunk_number']

    @resumable_chunk_number.setter
    def resumable_chunk_number(self, resumable_chunk_number):
        self._attribute_map['resumable_chunk_number'] = resumable_chunk_number

    @property
    def resumable_total_chunks(self):
        return self._attribute_map['resumable_total_chunks']

    @resumable_total_chunks.setter
    def resumable_total_chunks(self, resumable_total_chunks):
        self._attribute_map['resumable_total_chunks'] = resumable_total_chunks

    @property
    def resumable_relative_path(self):
        return self._attribute_map['resumable_relative_path']

    @resumable_relative_path.setter
    def resumable_relative_path(self, resumable_relative_path):
        self._attribute_map['resumable_relative_path'] = resumable_relative_path.rstrip('/')

    @property
    def resumable_total_size(self):
        return self._attribute_map['resumable_total_size']

    @resumable_total_size.setter
    def resumable_total_size(self, resumable_total_size):
        self._attribute_map['resumable_total_size'] = resumable_total_size

    @property
    def tags(self):
        return self._attribute_map['tags']

    @tags.setter
    def tags(self, tags):
        self._attribute_map['tags'] = tags

    @property
    def uploader(self):
        return self._attribute_map['uploader']

    @uploader.setter
    def uploader(self, uploader):
        self._attribute_map['uploader'] = uploader

    @property
    def metadatas(self):
        return self._attribute_map['metadatas']

    @metadatas.setter
    def metadatas(self, metadatas):
        self._attribute_map['metadatas'] = metadatas


def generate_pre_upload_form(
    project_code,
    operator,
    file_upload_form: FileUploadForm,
    zone,
    job_type,
    upload_message,
    current_folder_node=''
):
    data = []
    for file in file_upload_form.resumable_filename:
        file_name = os.path.basename(file)
        relative_file_path = get_relative_path(file, current_folder_node,
                                               file_upload_form.resumable_relative_path, job_type)
        data.append(
            {
                'resumable_filename': file_name,
                'resumable_relative_path': relative_file_path
            })
    return {
        'project_code': project_code,
        'operator': operator,
        'upload_message': upload_message,
        'job_type': job_type,
        'zone': zone,
        'current_folder_node': current_folder_node,
        'data': data,
        'filename': file_name
    }


def get_relative_path(file, current_folder_node, resumable_relative_path, job_type):
    relative_file_path = '/'.join(os.path.relpath(file).split('/')[0:-1])
    relative_file_path = relative_file_path[relative_file_path.index(resumable_relative_path):]
    if current_folder_node == '':
        relative_file_path = relative_file_path
    elif job_type == 'AS_FOLDER':
        relative_file_path = current_folder_node + '/' + '/'.join(relative_file_path.split('/')[1:])
    else:
        relative_file_path = current_folder_node
    return relative_file_path.rstrip('/')


def generate_chunk_form(project_code, operator, file_upload_form: FileUploadForm, chunk_number: int):
    my_form = {
        "project_code": project_code,
        "operator": operator,
        "resumable_identifier": file_upload_form.resumable_identifier,
        "resumable_filename": file_upload_form.resumable_filename,
        "resumable_relative_path": file_upload_form.resumable_relative_path,
        "resumable_dataType": "SINGLE_FILE_DATA",
        "resumable_chunk_number": int(chunk_number),
        "resumable_chunk_size": AppConfig.Env.chunk_size,
        "resumable_total_chunks": int(file_upload_form.resumable_total_chunks),
        "resumable_total_size": int(file_upload_form.resumable_total_size),
        "tags": file_upload_form.tags
    }
    return my_form


def generate_on_success_form(project_code, operator, file_upload_form: FileUploadForm,
                             from_parents=None, process_pipeline=None, upload_message=None):
    my_form = {
        "project_code": project_code,
        "operator": operator,
        "resumable_identifier": file_upload_form.resumable_identifier,
        "resumable_dataType": "SINGLE_FILE_DATA",
        "resumable_filename": file_upload_form.resumable_filename,
        "resumable_total_chunks": file_upload_form.resumable_total_chunks,
        "resumable_total_size": file_upload_form.resumable_total_size,
        "resumable_relative_path": file_upload_form.resumable_relative_path,
        "tags": file_upload_form.tags
    }
    if from_parents:
        my_form['from_parents'] = from_parents
    if process_pipeline:
        my_form['process_pipeline'] = process_pipeline
    if upload_message:
        my_form['upload_message'] = upload_message
    return my_form
