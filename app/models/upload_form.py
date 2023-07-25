# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from app.services.file_manager.file_upload.models import FileObject


def generate_on_success_form(
    project_code: str,
    operator: str,
    file_object: FileObject,
    from_parents: str = None,
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
    }
    if from_parents:
        request_payload['from_parents'] = from_parents
    if upload_message:
        request_payload['upload_message'] = upload_message
    return request_payload
