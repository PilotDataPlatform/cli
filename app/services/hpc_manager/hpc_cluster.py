# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import HPCMetaService
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import resilient_session


class HPCPartitionManager(metaclass=HPCMetaService):
    def __init__(self):
        self.user = UserConfig()
        if self.user.hpc_token:
            self.token = self.user.hpc_token
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value='Invalid HPC token')
        self.username = self.user.username

    @require_valid_token('kong')
    def list_partitions(self, host):
        url = AppConfig.Connections.url_bff + '/v1/hpc/partitions'
        paramas = {'host': host, 'username': self.username, 'token': self.token}
        headers = {'Authorization': 'Bearer ' + self.user.access_token}
        res = resilient_session().get(url, headers=headers, params=paramas)
        _res = res.json()
        code = _res.get('code')
        if code == 200:
            _info = _res.get('result')
            return _info
        elif code == 400:
            error_msg = _res.get('error_msg')
            if 'HPC protocal required' in error_msg:
                error_detail = f'missing protocol in the host, try http://{host} or https://{host}'
            else:
                error_detail = 'Cannot list partitions, please verify your host and try again later'
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, alue='List partitions')

    @require_valid_token()
    def get_partition(self, host, partition_name):
        url = AppConfig.Connections.url_bff + f'/v1/hpc/partitions/{partition_name}'
        params = {'host': host, 'username': self.username, 'token': self.token, 'partition_name': partition_name}
        headers = {'Authorization': 'Bearer ' + self.user.access_token}
        res = resilient_session().get(url, headers=headers, params=params)
        _res = res.json()
        code = _res.get('code')
        if code == 200:
            result = _res.get('result')
            return result
        elif code == 400:
            error_msg = _res.get('error_msg')
            if 'HPC protocal required' in error_msg:
                error_detail = f'missing protocol in the host, try http://{host} or https://{host}'
            else:
                error_detail = 'Cannot get partition, please verify your partition name and try again later'
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)
        elif code == 404:
            error_detail = f'Partition {partition_name} may not exist'
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)
        else:
            error_detail = f'Get partition {partition_name}'
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)


class HPCNodeManager(metaclass=HPCMetaService):
    def __init__(self):
        self.user = UserConfig()
        if self.user.hpc_token:
            self.token = self.user.hpc_token
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value='Invalid HPC token')
        self.username = self.user.username

    @require_valid_token()
    def get_node(self, host, node_name):
        url = AppConfig.Connections.url_bff + f'/v1/hpc/nodes/{node_name}'
        params = {'host': host, 'username': self.username, 'token': self.token, 'node_name': node_name}
        headers = {'Authorization': 'Bearer ' + self.user.access_token}
        res = resilient_session().get(url, headers=headers, params=params)
        _res = res.json()
        code = _res.get('code')
        if code == 200:
            result = _res.get('result')
            return result
        elif code == 400:
            error_msg = _res.get('error_msg')
            if 'HPC protocal required' in error_msg:
                error_detail = f'missing protocol in the host, try http://{host} or https://{host}'
            else:
                error_detail = 'Cannot get node information, please verify your node name and try again later'
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)
        elif code == 404:
            error_detail = f'Node {node_name} may not exist'
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)
        else:
            error_detail = f'Get node {node_name}'
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)

    @require_valid_token()
    def list_nodes(self, host):
        url = AppConfig.Connections.url_bff + '/v1/hpc/nodes'
        paramas = {'host': host, 'username': self.username, 'token': self.token}
        headers = {'Authorization': 'Bearer ' + self.user.access_token}
        res = resilient_session().get(url, headers=headers, params=paramas)
        _res = res.json()
        code = _res.get('code')
        if code == 200:
            _info = _res.get('result')
            return _info
        elif code == 400:
            error_msg = _res.get('error_msg')
            if 'HPC protocal required' in error_msg:
                error_detail = f'missing protocol in the host, try http://{host} or https://{host}'
            else:
                error_detail = 'Cannot list nodes, please verify your host and try again later'
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)
        else:
            SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value='List nodes')
