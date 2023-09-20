# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import re

import requests

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.error_handler import customized_error_msg
from app.services.user_authentication.decorator import require_valid_token


class SrvFileTag(metaclass=MetaService):
    appconfig = AppConfig()
    user = UserConfig()

    def __init__(self, interactive=True):
        self.interactive = interactive

    @staticmethod
    def validate_tag(tag):
        tag_requirement = re.compile('^[a-z0-9-]{1,32}$')
        if tag == 'copied-to-core':
            return False, ECustomizedError.RESERVED_TAG
        elif not re.search(tag_requirement, tag):
            return False, ECustomizedError.INVALID_TAG_ERROR
        else:
            return True, ''

    def validate_taglist(self, tag_list):
        validate_list_result = list(map(self.validate_tag, list(tag_list)))
        invalid_tag = []
        _validation_error = ''
        for i in range(len(validate_list_result)):
            if not validate_list_result[i][0]:
                invalid_tag.append(tag_list[i])
                _validation_error = validate_list_result[i][1]
        if _validation_error:
            pass
        elif len(tag_list) != len(set(tag_list)):
            _validation_error = ECustomizedError.DUPLICATE_TAG_ERROR
        elif len(tag_list) > 10:
            _validation_error = ECustomizedError.LIMIT_TAG_ERROR
        else:
            return True, ''
        if self.interactive:
            SrvErrorHandler.customized_handle(_validation_error, True)
        else:
            error = customized_error_msg(_validation_error)
            return False, error

    @require_valid_token()
    def add_tag(self, tags: list, geid: str):
        payload = {'taglist': tags, 'geid': geid}
        payload = {'tags': tags, 'inherit': False}
        headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
        }
        url = self.appconfig.Connections.url_file_tag % geid
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            result = res.json()['result']
            return True, result
        else:
            error_result = res.json()['error_msg'].upper().replace(' ', '_')
            _validation_error = getattr(ECustomizedError, error_result)
            if self.interactive:
                SrvErrorHandler.customized_handle(_validation_error, True)
            else:
                error = customized_error_msg(_validation_error)
                return False, error
