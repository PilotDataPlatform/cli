# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from app.services.dataset_manager.dataset_list import SrvDatasetListManager


def test_list_datasets(httpx_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    httpx_mock.add_response(
        method='GET',
        url='http://bff_cli/v1/datasets?page=1&page_size=10',
        json={
            'code': 200,
            'error_msg': '',
            'result': [
                {'id': 'fake-id1', 'code': 'testdataset1', 'title': 'testdatasetA', 'creator': 'test-user'},
                {'id': 'fake-id2', 'code': 'testdataset2', 'title': 'testdatasetB', 'creator': 'test-user'},
                {'id': 'fake-id3', 'code': 'testdataset3', 'title': 'testdatasetC', 'creator': 'test-user'},
            ],
        },
    )
    dataset_mgr = SrvDatasetListManager()
    dataset_mgr.list_datasets(page=1, page_size=10)
    out, err = capsys.readouterr()
    print_out = out.split('\n')
    assert print_out[0] == '             Dataset Title                            Dataset Code              '
    assert print_out[1] == '---------------------------------------------------------------------------'
    assert print_out[2] == '              testdatasetA               |             testdataset1            '
    assert print_out[3] == '              testdatasetB               |             testdataset2            '
    assert print_out[4] == '              testdatasetC               |             testdataset3            '
    assert print_out[5] == ''
    assert print_out[6] == 'Page: 1, Number of datasets: 3'
