# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

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
        'action_type': lineage_event['action_type'],
        'input_path': lineage_event['input_path'],
        'output_path': lineage_event['output_path'],
        'description': 'straight upload by ' + lineage_event['operator'],
    }
    headers = {
        'Authorization': 'Bearer ' + lineage_event['token'],
    }
    __res = requests.post(url, json=payload, headers=headers)
    if __res.status_code == 200:
        return __res.json()['result']
    else:
        SrvErrorHandler.customized_handle(
            ECustomizedError.INVALID_LINEAGE, True, value=str(__res.status_code) + str(__res.text)
        )
