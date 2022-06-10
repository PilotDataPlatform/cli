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

from app.utils.aggregated import search_item

test_project_code = 'testproject'


def test_search_file_should_return_200(requests_mock, mocker):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.check_valid',
        return_value=0
    )
    requests_mock.get(
        f"http://bff_cli/v1/project/{test_project_code}/search",
        json={
            "code": 200,
            "error_msg": "",
            "result": {
                "id": "file-id",
                "parent": 'parent-id',
                "parent_path": 'folder1',
                "restore_path": None,
                "archived": False,
                "type": "file",
                "zone": 0,
                "name": "test-file",
                "size": 1048576,
                "owner": "admin",
                "container_code": test_project_code,
                "container_type": "project",
                "created_time": "2021-07-02 16:34:09.164000",
                "last_updated_time": "2021-07-02 16:34:09.164000",
                "storage": {
                    'id': 'storage-id',
                    'location_uri': 'minio-path',
                    'version': 'version-id'
                },
                "extended": {
                    "id": "extended-id",
                    "extra": {"tags": [], "system_tags": [], "attributes": {}}
                }
            }
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
        'storage': {
            'id': 'storage-id',
            'location_uri': 'minio-path',
            'version': 'version-id'
        },
        'extended': {
            'id': 'extended-id',
            'extra': {'tags': [], 'system_tags': [], 'attributes': {}}
        }
    }
    res = search_item(test_project_code, 'zone', 'folder_relative_path', 'file', 'token', 'project')
    assert res == expected_result
