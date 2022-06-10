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
from app.services.user_authentication.user_login_logout import user_login, check_is_login
from app.services.output_manager.error_handler import ECustomizedError
from app.resources.custom_error import Error
from app.configs.user_config import UserConfig

def test_user_login_success(requests_mock):
    requests_mock.post('http://service_auth', 
        json={
            'code': 200, 
            'error_msg': '', 
            'page': 0, 
            'total': 1, 
            'num_of_pages': 1, 
            'result': {
                'access_token': 'fake-token', 
                'expires_in': 300, 
                'refresh_expires_in': 360, 
                'refresh_token': 'refresh-token', 
                'token_type': 'Bearer', 
                'not-before-policy': 0, 
                'session_state': 'session-state', 
                'scope': 'roles groups profile email'
                }
            },
    )
    res = user_login('username', 'password')
    assert res.get('code') == 200
    assert res['result'].get('access_token') == "fake-token"
    assert res['result'].get('refresh_token') == "refresh-token"
    assert res.get('error_msg') == ""

def test_user_login_wrong_password(requests_mock, capsys):
    requests_mock.post('http://service_auth', 
        json={
            "code":401,
            "error_msg":"401: b'{\"error\":\"invalid_grant\",\"error_description\":\"Invalid user credentials\"}'",
            "page":0,
            "total":1,
            "num_of_pages":1,
            "result":[]
            },
        status_code=401
    )
    with pytest.raises(SystemExit):
        user_login('username', 'password')
    out, err = capsys.readouterr()
    assert out == Error.error_msg.get(ECustomizedError.INVALID_CREDENTIALS.name, "Unknown error.") + '\n'
    assert err == ''

def test_check_is_not_login(mocker):
    mocker.patch(
        'configparser.ConfigParser.has_option',
        return_value = False
    )
    with pytest.raises(SystemExit):
        actual = check_is_login()
        assert actual == False
