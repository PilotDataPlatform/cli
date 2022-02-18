import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from app.configs.app_config import AppConfig
import app.services.output_manager.error_handler as ehandler


def create_lineage(child_file_geid, parent_file_geid, token: str,
                   project_code, pipeline_name, operator):
    url = AppConfig.Connections.url_bff + "/v1/lineage"
    payload = {
        "input_geid": parent_file_geid,
        "output_geid": child_file_geid,
        "project_code": project_code,
        "pipeline_name": pipeline_name,
        "description": "straight upload by " + operator
    }
    headers = {
        'Authorization': "Bearer " + token,
    }
    __res = requests.post(url, json=payload, headers=headers)
    if __res.status_code == 200:
        return __res.json()['result']
    else:
        ehandler.SrvErrorHandler.customized_handle(
            ehandler.ECustomizedError.INVALID_LINEAGE,
            True, value=str(__res.status_code) + str(__res.text))
