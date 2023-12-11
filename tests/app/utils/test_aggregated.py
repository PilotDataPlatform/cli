# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pytest

from app.utils.aggregated import search_item

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
