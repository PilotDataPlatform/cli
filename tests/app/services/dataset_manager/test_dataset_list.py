# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from app.services.dataset_manager.dataset_list import SrvDatasetListManager


def mock_dataset_list(num_datasets: int):
    return [
        {'id': f'fake-id{i}', 'code': f'testdataset{i}', 'title': f'testdataset{i}', 'creator': 'test-user'}
        for i in range(1, num_datasets + 1)
    ]


def test_list_datasets(httpx_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    httpx_mock.add_response(
        method='GET',
        url='http://bff_cli/v1/datasets?page=0&page_size=10',
        json={
            'code': 200,
            'error_msg': '',
            'result': mock_dataset_list(3),
            'total': 3,
            'page': 1,
        },
    )
    dataset_mgr = SrvDatasetListManager()
    dataset_mgr.list_datasets(page=0, page_size=10)
    out, err = capsys.readouterr()
    print_out = out.split('\n')
    assert print_out[0] == '             Dataset Title                            Dataset Code              '
    assert print_out[1] == '---------------------------------------------------------------------------'
    assert print_out[2] == '              testdataset1               |             testdataset1            '
    assert print_out[3] == '              testdataset2               |             testdataset2            '
    assert print_out[4] == '              testdataset3               |             testdataset3            '
    assert print_out[5] == ''
    assert print_out[6] == 'Page: 0, Number of datasets in page: 3, Total number of datasets: 3'


def test_list_datasets_no_datasets(httpx_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    httpx_mock.add_response(
        method='GET',
        url='http://bff_cli/v1/datasets?page=0&page_size=10',
        json={
            'code': 200,
            'error_msg': '',
            'result': [],
            'total': 0,
            'page': 1,
        },
    )
    dataset_mgr = SrvDatasetListManager()
    dataset_mgr.list_datasets(page=0, page_size=10)
    out, err = capsys.readouterr()
    print_out = out.split('\n')
    assert print_out[0] == '             Dataset Title                            Dataset Code              '
    assert print_out[1] == '---------------------------------------------------------------------------'
    assert print_out[2] == ''
    assert print_out[3] == 'Page: 0, Number of datasets in page: 0, Total number of datasets: 0'


def test_list_datasets_order_by_code_desc(httpx_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    mock_datasets = mock_dataset_list(3)
    mock_datasets.sort(key=lambda x: x['code'], reverse=True)
    httpx_mock.add_response(
        method='GET',
        url='http://bff_cli/v1/datasets?page=0&page_size=10',
        json={
            'code': 200,
            'error_msg': '',
            'result': mock_datasets,
            'total': 3,
            'page': 1,
        },
    )
    dataset_mgr = SrvDatasetListManager()
    dataset_mgr.list_datasets(page=0, page_size=10)
    out, err = capsys.readouterr()
    print_out = out.split('\n')
    assert print_out[0] == '             Dataset Title                            Dataset Code              '
    assert print_out[1] == '---------------------------------------------------------------------------'
    assert print_out[2] == '              testdataset3               |             testdataset3            '
    assert print_out[3] == '              testdataset2               |             testdataset2            '
    assert print_out[4] == '              testdataset1               |             testdataset1            '
    assert print_out[5] == ''
    assert print_out[6] == 'Page: 0, Number of datasets in page: 3, Total number of datasets: 3'
