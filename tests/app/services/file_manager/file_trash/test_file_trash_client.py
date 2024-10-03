# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pytest
from httpx import HTTPStatusError

from app.configs.app_config import AppConfig
from app.models.item import ItemStatus
from app.services.file_manager.file_trash.file_trash_client import FileTrashClient
from tests.conftest import decoded_token


@pytest.mark.parametrize('status_code', [400, 403, 404, 500])
def test_trash_api_error_handling(httpx_mock, status_code):
    test_project_code = 'test_code'
    test_parent_id = 'test_parent_id'
    test_object_ids = ['test_object_id']
    test_zone = 'greenroom'

    httpx_mock.add_response(
        url=AppConfig.Connections.url_bff
        + f'/v1/{test_project_code}/files?source_id={test_parent_id}&zone={test_zone}&target_ids={test_object_ids[0]}',
        method='DELETE',
        status_code=status_code,
        json={},
    )

    file_trash_client = FileTrashClient(
        project_code=test_project_code, parent_id=test_parent_id, object_ids=test_object_ids, zone=test_zone
    )

    try:
        file_trash_client.move_to_trash()
    except HTTPStatusError as e:
        assert e.response.status_code == status_code
    else:
        raise AssertionError()


@pytest.mark.parametrize('status_code', [400, 403, 404, 500])
def test_permanent_delete_error_handling(httpx_mock, status_code):
    test_project_code = 'test_code'
    test_parent_id = 'test_parent_id'
    test_object_ids = ['test_object_id']
    test_zone = 'greenroom'

    httpx_mock.add_response(
        url=AppConfig.Connections.url_bff
        + f'/v1/{test_project_code}/files/purge?zone={test_zone}&target_ids={test_object_ids[0]}',
        method='DELETE',
        status_code=status_code,
        json={},
    )

    file_trash_client = FileTrashClient(
        project_code=test_project_code, parent_id=test_parent_id, object_ids=test_object_ids, zone=test_zone
    )

    try:
        file_trash_client.permanently_delete()
    except HTTPStatusError as e:
        assert e.response.status_code == status_code
    else:
        assert AssertionError()


@pytest.mark.parametrize('file_status', [ItemStatus.TRASHED, ItemStatus.DELETED])
def test_check_file_status(mocker, httpx_mock, file_status):
    test_project_code = 'test_code'
    test_parent_id = 'test_parent_id'
    test_object_ids = ['test_object_id']
    test_zone = 'greenroom'

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    httpx_mock.add_response(
        url=AppConfig.Connections.url_bff + '/v1/query/geid',
        method='POST',
        status_code=200,
        json={
            'result': [
                {
                    'result': {
                        'id': 'test_object_id',
                        'status': str(file_status),
                        'name': 'test_name',
                        'parent_id': 'test_parent_id',
                        'parent_path': 'test_parent_path',
                        'restore_path': 'test_restore_path',
                    },
                    'status': str(file_status),
                }
            ]
        },
    )

    file_trash_client = FileTrashClient(
        project_code=test_project_code, parent_id=test_parent_id, object_ids=test_object_ids, zone=test_zone
    )
    file_trash_client.retry_interval = 1
    file_trash_client.max_status_check = 1

    res = file_trash_client.check_status(file_status)
    if file_status == ItemStatus.ACTIVE:
        assert res == ['test_parent_path/test_name']
    else:
        assert res == []
