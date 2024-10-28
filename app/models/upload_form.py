# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from app.services.file_manager.file_upload.models import FileObject


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


def generate_on_success_form(
    project_code: str,
    operator: str,
    file_object: FileObject,
    tags: list[str],
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
        'item_id': file_object.item_id,
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
