# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pytest

from app.services.dataset_manager.dataset_detail import SrvDatasetDetailManager
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import customized_error_msg

test_dataset_code = 'test_code'


def test_get_dataset_detail(httpx_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    httpx_mock.add_response(
        method='GET',
        url=f'http://bff_cli/v1/dataset/{test_dataset_code}?page=0&page_size=10',
        json={
            'code': 200,
            'error_msg': '',
            'result': {
                'general_info': {
                    'id': 'fake-id',
                    'source': '',
                    'authors': ['test-admin', 'test-user'],
                    'code': test_dataset_code,
                    'type': 'GENERAL',
                    'modality': [],
                    'collection_method': [],
                    'license': '',
                    'tags': ['cdsa'],
                    'description': 'Description example.',
                    'size': 25,
                    'total_files': 1,
                    'title': 'test dataset',
                    'creator': 'test-admin',
                    'project_id': 'project-id',
                    'created_at': '2022-02-03T19:49:35',
                    'updated_at': '2022-03-18T18:08:33',
                },
                'version_detail': [],
                'version_no': 0,
            },
        },
    )
    dataset_mgr = SrvDatasetDetailManager()
    dataset_mgr.dataset_detail(test_dataset_code)
    out, _ = capsys.readouterr()
    print_out = out.split('\n')
    assert print_out[0] == '--------------------------------------------------------------------------------'
    assert print_out[1] == '|        Title        |                       test dataset                     |'
    assert print_out[2] == '--------------------------------------------------------------------------------'
    assert print_out[3] == '|         Code        |                        test_code                       |'
    assert print_out[4] == '--------------------------------------------------------------------------------'
    assert print_out[5] == '|       Authors       |                  test-admin, test-user                 |'
    assert print_out[6] == '--------------------------------------------------------------------------------'
    assert print_out[7] == '|         Type        |                         GENERAL                        |'
    assert print_out[8] == '--------------------------------------------------------------------------------'
    assert print_out[9] == '|       Modality      |                                                        |'
    assert print_out[10] == '--------------------------------------------------------------------------------'
    assert print_out[11] == '|  Collection_method  |                                                        |'
    assert print_out[12] == '--------------------------------------------------------------------------------'
    assert print_out[13] == '|         Tags        |                           cdsa                         |'
    assert print_out[14] == '--------------------------------------------------------------------------------'
    assert print_out[15] == '|       Versions      |                                                        |'
    assert print_out[16] == '--------------------------------------------------------------------------------'


def test_get_dataset_detail_not_exist(httpx_mock, mocker, capsys):
    fake_dataset_code = 'fake-code'
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    httpx_mock.add_response(
        method='GET',
        url=f'http://bff_cli/v1/dataset/{fake_dataset_code}?page=0&page_size=10',
        json={'code': 404, 'error_msg': 'Cannot found given dataset code', 'result': {}},
        status_code=404,
    )
    with pytest.raises(SystemExit):
        dataset_mgr = SrvDatasetDetailManager()
        dataset_mgr.dataset_detail(fake_dataset_code)
    out, _ = capsys.readouterr()
    assert out.rstrip('\n') == customized_error_msg(ECustomizedError.DATASET_NOT_EXIST)


def test_get_dataset_detail_not_access(httpx_mock, mocker, capsys):
    fake_dataset_code = 'restrict-code'
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    httpx_mock.add_response(
        method='GET',
        url=f'http://bff_cli/v1/dataset/{fake_dataset_code}?page=0&page_size=10',
        json={'code': 403, 'error_msg': 'Permission Denied', 'result': {}},
        status_code=403,
    )
    with pytest.raises(SystemExit):
        dataset_mgr = SrvDatasetDetailManager()
        dataset_mgr.dataset_detail(fake_dataset_code)
    out, _ = capsys.readouterr()
    assert out.rstrip('\n') == customized_error_msg(ECustomizedError.DATASET_PERMISSION)
