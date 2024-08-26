# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pytest

from app.services.file_manager.file_metadata.folder_client import FolderClient


def test_get_root_folder_id_success(mocker):
    project_code = 'project_code'
    zone = 'greenroom'
    root_folder = 'root_folder'
    exist_parent_id = 'exist_parent_id'

    search_item_mock = mocker.patch('app.services.file_manager.file_metadata.folder_client.search_item')
    search_item_mock.return_value = {'result': {'id': exist_parent_id}}
    folder_client = FolderClient(project_code, zone)

    assert folder_client._get_root_folder_id(root_folder) == exist_parent_id
    search_item_mock.assert_called_once_with(project_code, 0, root_folder)


def test_get_root_folder_id_fail(mocker):
    project_code = 'project_code'
    zone = 'greenroom'
    root_folder = 'root_folder'

    search_item_mock = mocker.patch('app.services.file_manager.file_metadata.folder_client.search_item')
    search_item_mock.return_value = {'result': {}}
    folder_client = FolderClient(project_code, zone)

    with pytest.raises(SystemExit):
        folder_client._get_root_folder_id(root_folder)
    search_item_mock.assert_called_once_with(project_code, 0, root_folder)


def test_create_folder(mocker, httpx_mock):
    project_code = 'project_code'
    zone = 'greenroom'
    folder_path = 'users/user/test'
    exist_parent_id = 'exist_parent_id'

    duplication_mock = mocker.patch(
        'app.services.file_manager.file_metadata.folder_client.check_item_duplication',
        return_value=['users', 'users/user'],
    )
    folder_client = FolderClient(project_code, zone)
    folder_client._get_root_folder_id = mocker.Mock(return_value=exist_parent_id)

    httpx_mock.add_response(
        url=f'{folder_client.endpoint}/folders/batch',
        json={'result': {'id': 'folder_id'}},
    )

    folder = folder_client.create_folder(folder_path)
    assert folder == {'id': 'folder_id'}

    duplication_mock.assert_called_once_with(['users/user/test'], 0, 'project_code')
    folder_client._get_root_folder_id.assert_called_once_with('users/user')
