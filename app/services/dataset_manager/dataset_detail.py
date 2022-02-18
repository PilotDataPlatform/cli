from app.models.service_meta_class import MetaService
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from ..user_authentication.decorator import require_valid_token
import requests
import app.services.logger_services.log_functions as logger
from app.services.output_manager.error_handler import SrvErrorHandler, ECustomizedError



class SrvDatasetDetailManager(metaclass=MetaService):
    def __init__(self, interactive=True):
        self.user = UserConfig()
        self.interactive = interactive

    @require_valid_token()
    def dataset_detail(self, code):
        url = AppConfig.Connections.url_bff + f'/v1/dataset/{code}'
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
        }
        try:
            response = requests.get(url, headers=headers)
            res = response.json()
            status_code = res.get('code')
            if status_code == 200:
                result = res.get('result')
                self.format_dataset_detail(result) if self.interactive else None
                return result
            elif status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.DATASET_NOT_EXIST, self.interactive)
            elif status_code == 403:
                SrvErrorHandler.customized_handle(ECustomizedError.DATASET_PERMISSION, self.interactive)
            else:
                SrvErrorHandler.default_handle(response.content, self.interactive)
        except Exception as e:
            SrvErrorHandler.default_handle(response.content, self.interactive)

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
                name_location = round(len(v.split(','))/2) - 1
                location = 0
                for i in v.split(','):
                    i = i if i == v.split(',')[-1] else i + ', '
                    if location == name_location:
                        row_value = '| ' + k.center(20,' ') + '| ' + i.center(value_width, ' ')
                    else:
                        row_value = '| ' + ''.center(20,' ') + '| ' + i.center(value_width, ' ')
                    location += 1
                    logger.info(row_value + '|')
            elif len(v) > value_width and k in same_line_display_fields:
                name_location = round(len(v)/(2*value_width)) - 1
                location = 0
                current_value = ''
                for i in v.split(',') + [' ' * 100000]:
                    if len(current_value + i + ', ') > value_width:
                        field_name = k if location == name_location else ''
                        row_value = '| ' + field_name.center(20,' ') + '| ' + current_value.center(value_width, ' ')
                        logger.info(row_value + '|')
                        current_value = i if i == v.split(',')[-1] else i + ', '
                        location += 1
                    else:
                        current_value = current_value + i  if i == v.split(',')[-1] else current_value + i + ', '
            else:
                row_value = '| ' + k.center(20,' ') + '| ' + v.replace(',', ', ').center(value_width, ' ')
                logger.info(row_value + '|')
        logger.info('-'.ljust(col_width, '-'))

