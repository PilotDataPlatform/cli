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

import pytest
from app.services.hpc_manager.hpc_auth import HPCTokenManager

def test_hpc_auth(requests_mock, mocker):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.check_valid',
        return_value = 0
    )
    requests_mock.post('http://bff_cli' + '/v1/hpc/auth', 
        json={
            "code":200,
            "error_msg":"",
            "result": "fake-token"
            }
    )
    hpc_mgr = HPCTokenManager('fake_token')
    token = hpc_mgr.auth_user('test_host', 'test_user', 'test_password')
    assert token == 'fake-token'

def test_hpc_auth_failed(requests_mock, mocker, capsys):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.check_valid',
        return_value = 0
    )
    requests_mock.post('http://bff_cli' + '/v1/hpc/auth', 
        json={
            "code":500,
            "error_msg":"User authorization failed: Authentication failed.",
            "result":[]
            }
    )
    hpc_mgr = HPCTokenManager('fake_token')
    with pytest.raises(SystemExit):
        hpc_mgr.auth_user('test_host', 'test_user', 'test_password')
    out, err = capsys.readouterr()
    assert out == 'Cannot proceed with HPC authorization request\n'
