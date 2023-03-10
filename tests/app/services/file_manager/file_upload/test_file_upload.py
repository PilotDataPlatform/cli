# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

from app.services.file_manager.file_upload.file_upload import assemble_path


def test_assemble_path_at_name_folder(mocker):
    local_file_path = './test/file.txt'
    target_folder = 'admin'
    project_code = 'test_project'
    zone = 0
    resumable_id = None

    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.search_item',
        return_value={
            'result': {
                'id': 'test',
                'parent_id': 'test_parent',
                'parent_path': '',
                'name': 'admin',
                'zone': 0,
            }
        },
    )

    current_file_path, parent_folder, create_folder_flag, _ = assemble_path(
        local_file_path, target_folder, project_code, zone, resumable_id
    )
    assert current_file_path == 'admin/file.txt'
    assert parent_folder.get('name') == 'admin'
    assert create_folder_flag is False


def test_assemble_path_at_exsting_folder(mocker):
    local_file_path = './test/file.txt'
    target_folder = 'admin/test_folder_exist'
    project_code = 'test_project'
    zone = 0
    resumable_id = None

    node_list = [
        {
            'result': {
                'id': 'test',
                'parent_id': 'test_parent',
                'parent_path': '',
                'name': 'admin',
                'zone': 0,
            }
        },
        {
            'result': {
                'id': 'test',
                'parent_id': 'test_parent',
                'parent_path': 'admin',
                'name': 'test_folder_exist',
                'zone': 0,
            }
        },
    ]

    mocker.patch('app.services.file_manager.file_upload.file_upload.search_item', side_effect=node_list)

    current_file_path, parent_folder, create_folder_flag, _ = assemble_path(
        local_file_path, target_folder, project_code, zone, resumable_id
    )
    assert current_file_path == 'admin/test_folder_exist/file.txt'
    assert parent_folder.get('name') == 'test_folder_exist'
    assert create_folder_flag is False


def test_assemble_path_at_non_existing_folder(mocker):
    local_file_path = './test/file.txt'
    target_folder = 'admin/test_folder_not_exist'
    project_code = 'test_project'
    zone = 0
    resumable_id = None

    node_list = [
        {
            'result': {
                'id': 'test',
                'parent_id': 'test_parent',
                'parent_path': '',
                'name': 'admin',
                'zone': 0,
            }
        },
        {'result': {}},
    ]

    mocker.patch('app.services.file_manager.file_upload.file_upload.search_item', side_effect=node_list)
    mocker.patch('app.services.file_manager.file_upload.file_upload.click.confirm', return_value=None)

    current_file_path, parent_folder, create_folder_flag, _ = assemble_path(
        local_file_path, target_folder, project_code, zone, resumable_id
    )
    assert current_file_path == 'admin/test_folder_not_exist/file.txt'
    assert parent_folder.get('name') == 'admin'
    assert create_folder_flag is True