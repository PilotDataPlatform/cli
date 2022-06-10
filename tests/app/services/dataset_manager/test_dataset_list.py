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

from app.services.dataset_manager.dataset_list import SrvDatasetListManager


def test_list_datasets(requests_mock, mocker, capsys):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.check_valid',
        return_value = 0
    )
    requests_mock.get('http://bff_cli' + '/v1/datasets', 
        json={
            "code":200,
            "error_msg":"",
            "result":[
                {
                    'id': 'fake-id1',
                    'code': 'testdataset1',
                    'title': 'testdatasetA',
                    'creator': 'test-user'
                },
                {
                    'id': 'fake-id2',
                    'code': 'testdataset2',
                    'title': 'testdatasetB',
                    'creator': 'test-user'
                },
                {
                    'id': 'fake-id3',
                    'code': 'testdataset3',
                    'title': 'testdatasetC',
                    'creator': 'test-user'
                }
            ]
        }
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
