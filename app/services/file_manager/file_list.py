from app.configs.app_config import AppConfig
import app.services.logger_services.log_functions as logger
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler
import requests
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.user_authentication.decorator import require_valid_token
from app.utils.aggregated import get_folder_in_project


class SrvFileList(metaclass=MetaService):
    user = UserConfig()

    @require_valid_token()
    def list_files(self, paths, zone):
        project_path = paths.strip('/').split('/')
        project_code = project_path[0]
        folder_rel_path = '/'.join(project_path[1:])
        if len(project_path) == 1:
            source_type = 'Container'
        else:
            source_type = 'Folder'
            res = get_folder_in_project(project_code, zone, folder_rel_path, self.user.access_token)

        get_url = AppConfig.Connections.url_bff + f'/v1/{project_code}/files/query'
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
        }
        params = {'project_code': project_code,
                  'folder': folder_rel_path,
                  'source_type': source_type,
                  'zone': zone}
        response = requests.get(get_url, params=params, headers=headers)
        res_json = response.json()
        if res_json.get('code') == 403 and res_json.get('error_msg') != 'Folder not exist':
            SrvErrorHandler.customized_handle(ECustomizedError.PERMISSION_DENIED, True)
        elif res_json.get('error_msg') == 'Folder not exist':
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_FOLDER, True)
        elif res_json.get('code') == 404 and res_json.get('error_msg') == 'Project not found':
            SrvErrorHandler.customized_handle(ECustomizedError.PROJECT_DENIED, True)
        res = res_json.get('result')
        files = ''
        folders = ''
        for f in res:
            if 'File' in f.get('labels'):
                files = files + f.get('name') + ' ...'
            elif 'Folder' in f.get('labels'):
                folders = folders + f"\033[34m{f.get('name')}\033[0m ..."
        f_string = folders + files
        return f_string
