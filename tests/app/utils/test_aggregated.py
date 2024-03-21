# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pytest

from app.configs.app_config import AppConfig
from app.models.folder import FolderType
from app.utils.aggregated import check_item_duplication
from app.utils.aggregated import identify_target_folder
from app.utils.aggregated import search_item
from app.utils.aggregated import validate_folder_name
from tests.conftest import decoded_token

test_project_code = 'testproject'


def test_search_file_should_return_200(requests_mock, mocker):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    requests_mock.get(
        f'http://bff_cli/v1/project/{test_project_code}/search',
        json={
            'code': 200,
            'error_msg': '',
            'result': {
                'id': 'file-id',
                'parent': 'parent-id',
                'parent_path': 'folder1',
                'restore_path': None,
                'status': 'ACTIVE',
                'type': 'file',
                'zone': 0,
                'name': 'test-file',
                'size': 1048576,
                'owner': 'admin',
                'container_code': test_project_code,
                'container_type': 'project',
                'created_time': '2021-07-02 16:34:09.164000',
                'last_updated_time': '2021-07-02 16:34:09.164000',
                'storage': {'id': 'storage-id', 'location_uri': 'minio-path', 'version': 'version-id'},
                'extended': {'id': 'extended-id', 'extra': {'tags': [], 'system_tags': [], 'attributes': {}}},
            },
        },
        status_code=200,
    )
    expected_result = {
        'id': 'file-id',
        'parent': 'parent-id',
        'parent_path': 'folder1',
        'restore_path': None,
        'status': 'ACTIVE',
        'type': 'file',
        'zone': 0,
        'name': 'test-file',
        'size': 1048576,
        'owner': 'admin',
        'container_code': test_project_code,
        'container_type': 'project',
        'created_time': '2021-07-02 16:34:09.164000',
        'last_updated_time': '2021-07-02 16:34:09.164000',
        'storage': {'id': 'storage-id', 'location_uri': 'minio-path', 'version': 'version-id'},
        'extended': {'id': 'extended-id', 'extra': {'tags': [], 'system_tags': [], 'attributes': {}}},
    }
    res = search_item(test_project_code, 'zone', 'folder_relative_path', 'project')
    assert res['result'] == expected_result


def test_search_item_returns_response_when_status_code_is_404(requests_mock, mocker, fake):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    expected_response = {'result': {'id': fake.uuid4()}}
    requests_mock.get(
        f'http://bff_cli/v1/project/{test_project_code}/search',
        json=expected_response,
        status_code=404,
    )

    response = search_item(test_project_code, 'zone', 'folder_relative_path', 'project')

    assert response == expected_response


def test_search_file_error_handling_with_403(requests_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    requests_mock.get(
        f'http://bff_cli/v1/project/{test_project_code}/search',
        json={},
        status_code=403,
    )
    with pytest.raises(SystemExit):
        search_item(test_project_code, 'zone', 'folder_relative_path', 'project')
    out, _ = capsys.readouterr()
    assert (
        out.rstrip()
        == 'Permission denied. Please verify your role in the Project has permission to perform this action.'
    )


def test_search_file_error_handling_with_401(requests_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    requests_mock.get(
        f'http://bff_cli/v1/project/{test_project_code}/search',
        text='Authentication failed.',
        status_code=401,
    )
    with pytest.raises(SystemExit):
        search_item(test_project_code, 'zone', 'folder_relative_path', 'project')
    out, _ = capsys.readouterr()
    assert out.rstrip() == 'Your login session has expired. Please try again or log in again.'


def test_check_duplicate_fail_with_error_code(httpx_mock, mocker, capsys):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    httpx_mock.add_response(
        url=AppConfig.Connections.url_base + '/portal/v1/files/exists',
        method='POST',
        json={'error': 'internal server error'},
        status_code=500,
    )

    with pytest.raises(SystemExit):
        check_item_duplication(['test_path'], 0, 'test_project_code')
    out, _ = capsys.readouterr()
    assert out.rstrip() == '{"error": "internal server error"}'


@pytest.mark.parametrize('folder_name', ['/:?.\\*<>|”\'', ''.join(['1' for _ in range(101)])])
def test_validate_folder_name(folder_name):
    valid = validate_folder_name(folder_name)
    assert valid is False


@pytest.mark.parametrize(
    'input_path,expected_result',
    [
        ('project_code/username', ('project_code', FolderType.NAMEFOLDER, 'username')),
        ('project_code/username/folder1', ('project_code', FolderType.NAMEFOLDER, 'username/folder1')),
        ('project_code/projectfolder/folder1', ('project_code', FolderType.PROJECTFOLDER, 'folder1')),
        ('project_code/projectfolder/folder1/folder2', ('project_code', FolderType.PROJECTFOLDER, 'folder1/folder2')),
    ],
)
def test_identify_target_folder_success_with_different_path(mocker, input_path, expected_result):
    mocker.patch('app.utils.aggregated.validate_folder_name', return_value=True)
    result = identify_target_folder(input_path)
    assert result == expected_result


def test_identify_target_folder_fail_with_invalid_input(mocker):
    mocker.patch('app.utils.aggregated.validate_folder_name', return_value=False)
    with pytest.raises(SystemExit):
        identify_target_folder('project_code')
