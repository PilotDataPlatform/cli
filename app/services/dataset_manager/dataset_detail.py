# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from httpx import HTTPStatusError

import app.services.logger_services.log_functions as logger
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.clients.base_auth_client import BaseAuthClient
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler

from ..user_authentication.decorator import require_valid_token


class SrvDatasetDetailManager(BaseAuthClient, metaclass=MetaService):
    def __init__(self, interactive=True):
        super().__init__(AppConfig.Connections.url_bff)

        self.user = UserConfig()
        self.interactive = interactive
        self.endpoint = AppConfig.Connections.url_bff + '/v1'

    @require_valid_token()
    def dataset_detail(self, code, page=0, page_size=10):
        params = {'page': page, 'page_size': page_size}
        try:
            response = self._get(f'dataset/{code}', params=params)
        except HTTPStatusError as e:
            response = e.response
            if response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.DATASET_NOT_EXIST, self.interactive)
            elif response.status_code == 403:
                SrvErrorHandler.customized_handle(ECustomizedError.DATASET_PERMISSION, self.interactive)
            else:
                SrvErrorHandler.default_handle(response.content, True)

        result = response.json().get('result')
        self.format_dataset_detail(result) if self.interactive else None
        return result

    @staticmethod
    def format_dataset_detail(dataset_info):
        same_line_display_fields = ['Versions', 'Tags', 'Collection_method', 'Authors']
        generail_info = dataset_info.get('general_info')
        version_detail = dataset_info.get('version_detail')
        dataset_details = {}
        dataset_details['Title'] = generail_info.get('title')
        dataset_details['Code'] = generail_info.get('code')
        dataset_details['Authors'] = ','.join(generail_info.get('authors'))
        dataset_details['Type'] = generail_info.get('type')
        dataset_details['Modality'] = ','.join(generail_info.get('modality'))
        dataset_details['Collection_method'] = ','.join(generail_info.get('collection_method'))
        dataset_details['Tags'] = ','.join(generail_info.get('tags'))
        versions = []
        for v in version_detail:
            versions.append(v.get('version'))
        dataset_details['Versions'] = ','.join(versions)
        col_width = 80
        value_width = col_width - 25
        for k, v in dataset_details.items():
            logger.info('-'.ljust(col_width, '-'))
            if len(v) > value_width and k not in same_line_display_fields:
                name_location = round(len(v.split(',')) / 2) - 1
                location = 0
                for i in v.split(','):
                    i = i if i == v.split(',')[-1] else i + ', '
                    if location == name_location:
                        row_value = '| ' + k.center(20, ' ') + '| ' + i.center(value_width, ' ')
                    else:
                        row_value = '| ' + ''.center(20, ' ') + '| ' + i.center(value_width, ' ')
                    location += 1
                    logger.info(row_value + '|')  # noqa: G003
            elif len(v) > value_width and k in same_line_display_fields:
                name_location = round(len(v) / (2 * value_width)) - 1
                location = 0
                current_value = ''
                for i in v.split(',') + [' ' * 100000]:
                    if len(current_value + i + ', ') > value_width:
                        field_name = k if location == name_location else ''
                        row_value = '| ' + field_name.center(20, ' ') + '| ' + current_value.center(value_width, ' ')
                        logger.info(row_value + '|')  # noqa: G003
                        current_value = i if i == v.split(',')[-1] else i + ', '
                        location += 1
                    else:
                        current_value = current_value + i if i == v.split(',')[-1] else current_value + i + ', '
            else:
                row_value = '| ' + k.center(20, ' ') + '| ' + v.replace(',', ', ').center(value_width, ' ')
                logger.info(row_value + '|')  # noqa: G003
        logger.info('-'.ljust(col_width, '-'))
