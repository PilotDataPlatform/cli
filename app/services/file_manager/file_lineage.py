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

import requests

from app.configs.app_config import AppConfig
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler


def create_lineage(lineage_event):
    url = AppConfig.Connections.url_lineage
    payload = {
        'input_id': lineage_event['input_id'],
        'output_id': lineage_event['output_id'],
        'project_code': lineage_event['project_code'],
        'pipeline_name': lineage_event['pipeline_name'],
        'input_name': lineage_event['input_name'],
        'output_name': lineage_event['output_name'],
        'description': 'straight upload by ' + lineage_event['operator']
    }
    headers = {
        'Authorization': "Bearer " + lineage_event['token'],
    }
    __res = requests.post(url, json=payload, headers=headers)
    if __res.status_code == 200:
        return __res.json()['result']
    else:
        SrvErrorHandler.customized_handle(
            ECustomizedError.INVALID_LINEAGE, True, value=str(__res.status_code) + str(__res.text))
