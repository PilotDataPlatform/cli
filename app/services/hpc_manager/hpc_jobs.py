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

import json

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import HPCMetaService
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.response_handler import HPCJobInfoResponse
from app.services.output_manager.response_handler import HPCJobSubmitResponse
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import resilient_session


class HPCJobManager(metaclass=HPCMetaService):
    def __init__(self):
        self.user = UserConfig()
        self.token = self.user.hpc_token if self.user.hpc_token \
            else SrvErrorHandler.customized_handle(
                ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value='Invalid HPC token')
        self.username = self.user.username

    def pre_load_data(self, path):
        json_data = {}
        try:
            with open(path) as f:
                json_data = json.load(f)
                f.close()
        except json.decoder.JSONDecodeError:
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_ACTION, False, f"{path} is an invalid json file")
        except Exception:
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_ACTION, False, f"{path} is an invalid json file")
        return json_data

    @require_valid_token()
    def submit_job(self, host, path):
        url = AppConfig.Connections.url_bff + '/v1/hpc/job'
        job_info = self.pre_load_data(path)
        payload = {
            "host": host,
            "username": self.username,
            "token": self.token,
            "job_info": job_info
        }
        headers = {'Authorization': 'Bearer ' + self.user.access_token}
        res = resilient_session().post(url, headers=headers, json=payload)
        _res = res.json()
        code = _res.get('code')
        result = _res.get('result')
        _ = getattr(HPCJobSubmitResponse(payload, _res), f"return_{code}_response")()
        return result

    @require_valid_token()
    def get_job(self, host, job_id):
        url = AppConfig.Connections.url_bff + f'/v1/hpc/job/{job_id}'
        params = {
            "host": host,
            "username": self.username,
            "token": self.token
        }
        headers = {'Authorization': 'Bearer ' + self.user.access_token}
        response = resilient_session().get(url, headers=headers, params=params)
        _res = response.json()
        code = _res.get('code')
        result = _res.get('result')
        params['job_id'] = job_id
        _ = getattr(HPCJobInfoResponse(params, _res), f"return_{code}_response")()
        return result
