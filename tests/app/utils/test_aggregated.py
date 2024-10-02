# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

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
                'archived': False,
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
        'archived': False,
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
    res = search_item(test_project_code, 'zone', 'folder_relative_path', 'file', 'project')
    assert res['result'] == expected_result
