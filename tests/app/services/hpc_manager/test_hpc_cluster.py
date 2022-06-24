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

from app.configs.user_config import UserConfig
from app.resources.custom_error import Error
from app.services.hpc_manager.hpc_cluster import HPCPartitionManager
from app.services.output_manager.error_handler import ECustomizedError
from tests.conftest import decoded_token


def test_hpc_list_partitions(requests_mock, mocker):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token()
    )
    requests_mock.get(
        'http://bff_cli' + '/v1/hpc/partitions',
        json={
            "code": 200,
            "error_msg": "",
            "result": [
                {
                    "partition1": {
                        'nodes': ['hpc-node1'],
                        'tres': "cpu=2,mem=4G,node=1,billing=2"
                    }
                },
                {
                    "partition2": {
                        "nodes": ["hpc-node2"],
                        "tres": "cpu=1,mem=8G,node=1,billing=1"
                    }
                }
            ]
        }
    )
    expected_partitions = [
        {'partition1': {'nodes': ['hpc-node1'], 'tres': 'cpu=2,mem=4G,node=1,billing=2'}},
        {'partition2': {'nodes': ['hpc-node2'], 'tres': 'cpu=1,mem=8G,node=1,billing=1'}}
    ]
    hpc_mgr = HPCPartitionManager()
    partion = hpc_mgr.list_partitions('test_host')
    assert partion == expected_partitions


def test_hpc_list_partitions_no_token(mocker, capsys, monkeypatch):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token()
    )
    monkeypatch.setattr(UserConfig, 'hpc_token', '')
    with pytest.raises(SystemExit):
        hpc_mgr = HPCPartitionManager()
        _ = hpc_mgr.list_partitions('test_host')
    out, err = capsys.readouterr()
    assert out == Error.error_msg.get(ECustomizedError.CANNOT_PROCESS_HPC_JOB.name) % 'Invalid HPC token\n'
