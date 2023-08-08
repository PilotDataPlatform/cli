# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pytest

from app.services.hpc_manager.hpc_auth import HPCTokenManager


def test_hpc_auth(httpx_mock, mocker):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    httpx_mock.add_response(
        method='POST',
        url='http://bff_cli' + '/v1/hpc/auth',
        json={'code': 200, 'error_msg': '', 'result': 'fake-token'},
        status_code=200,
    )
    hpc_mgr = HPCTokenManager('fake_token')
    token = hpc_mgr.auth_user('test_host', 'test_user', 'test_password')
    assert token == 'fake-token'


def test_hpc_auth_failed(httpx_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    httpx_mock.add_response(
        method='POST',
        url='http://bff_cli' + '/v1/hpc/auth',
        json={'code': 500, 'error_msg': 'User authorization failed: Authentication failed.', 'result': []},
    )
    hpc_mgr = HPCTokenManager('fake_token')
    with pytest.raises(SystemExit):
        hpc_mgr.auth_user('test_host', 'test_user', 'test_password')
    out, err = capsys.readouterr()
    assert out == 'Cannot proceed with HPC authorization request\n'
