# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from os.path import basename
from os.path import dirname
from os.path import join
from typing import List

from app.services.file_manager.file_upload.models import FileObject
from app.services.file_manager.file_upload.models import UploadType


class FileUploadForm:
    def __init__(self):
        self._attribute_map = {
            'resumable_identifier': '',
            'resumable_filename': '',
            'resumable_chunk_number': -1,
            'resumable_total_chunks': -1,
            'resumable_total_size': -1,
            'resumable_relative_path': '',
            'tags': [],
            'uploader': '',
            'metadatas': None,
            'container_id': '',
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
    project_code: str,
    operator: str,
    local_file_paths: List[str],
    input_path: str,
    zone: str,
    job_type: UploadType,
    current_folder: str = '',
) -> tuple[dict, dict]:
    """
    Summary:
        The function is to generate the preupload payload for api. The operation
        is per batch that it will try to generate one payload for all files.
    Parameter:
        - project_code(str): The unique identifier for project.
        - operator(str): The name of operator.
        - local_file_paths(list[str]): The list of name for input files.
        - input_path: The path specified by user, if it is folder, it will be like
            a/b . If it is a file it will be same as local_file_paths eg. a/b/c.txt.
        - zone(str): The zone of user try to upload to.
        - job_type(UploadType): the upload type, AS_FOLDER or AS_FILE.
        - current_folder(str): the folder path on object storage that user specified.
    return:
        - request_payload(dict): the payload for preupload api.
        - local_file_mapping(dict): the mapping from object path into local path.
    """
    data, local_file_mapping = [], {}
    for file_local_path in local_file_paths:
        # the rule here is:
        # - if use input as a folder then <input_path> is the folder user key in
        #   eg. a/b/ . the <local_file_paths> is files under eg a/b/c/d.txt. The
        #   path in object storage will be <current_folder>/c/d.txt
        # - if use input as a file then <input_path> is the file user key in eg.
        #   a/b/c/d.txt. the <local_file_paths> will be same as it. The path in
        #   object storage will be <current_folder>/d.txt
        if job_type == UploadType.AS_FOLDER:
            file_relative_path = file_local_path.replace(input_path + '/', '')
            object_path = join(current_folder, file_relative_path)
            parent_path, file_name = dirname(object_path), basename(object_path)

        else:
            file_name = basename(file_local_path)
            parent_path = current_folder

        data.append({'resumable_filename': file_name, 'resumable_relative_path': parent_path})
        # make a mapping as <object_path>: <local_path>. This will be returned
        # and used in chunk upload api.
        object_path = join(parent_path, file_name)
        local_file_mapping.update({object_path: file_local_path})

    request_payload = {
        'project_code': project_code,
        'operator': operator,
        'job_type': str(job_type),
        'zone': zone,
        'current_folder_node': current_folder,
        'data': data,
    }

    return request_payload, local_file_mapping


def generate_on_success_form(
    project_code: str,
    operator: str,
    file_object: FileObject,
    tags: List[str],
    from_parents: str = None,
    process_pipeline: str = None,
    upload_message: str = None,
):
    """
    Summary:
        The function is to generate the payload of combine chunks api. The operation
        is per file that it will try to generate one payload for each file.
    Parameter:
        - project_code(str): The unique identifier for project.
        - operator(str): The name of operator.
        - file_object(FileObject): The object that contains the file information.
        - tags(list[str]): The tags that will be attached with file.
        - from_parents(str): indicate it is parent node.
        - process_pipeline(str): the name of pipeline.
        - upload_message(str): the message for uploading.
    return:
        - request_payload(dict): the payload for preupload api.
    """

    request_payload = {
        'project_code': project_code,
        'operator': operator,
        'job_id': file_object.job_id,
        'resumable_identifier': file_object.resumable_id,
        'resumable_dataType': 'SINGLE_FILE_DATA',
        'resumable_filename': file_object.file_name,
        'resumable_total_chunks': file_object.total_chunks,
        'resumable_total_size': file_object.total_size,
        'resumable_relative_path': file_object.parent_path,
        'tags': tags,
    }
    if from_parents:
        request_payload['from_parents'] = from_parents
    if process_pipeline:
        request_payload['process_pipeline'] = process_pipeline
    if upload_message:
        request_payload['upload_message'] = upload_message
    return request_payload
