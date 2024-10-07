# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from json import loads

import requests

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token


class SrvContainerRegistryMgr(metaclass=MetaService):
    def check_harbor_url_set(self):
        if not AppConfig.Connections.url_harbor or AppConfig.Connections.url_harbor == '':
            SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_NO_URL, self.interactive)

    def __init__(self, interactive=True):
        self.user = UserConfig()
        self.interactive = interactive
        requests.packages.urllib3.disable_warnings()
        self.check_harbor_url_set()

    def get_public(self, visibility: str) -> bool:
        if visibility == 'public':
            return True
        elif visibility == 'private':
            return False
        SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_VISIBILITY_INVALID, self.interactive)

    def get_role_number(self, role: str) -> int:
        if role == 'admin':
            return 1
        elif role == 'developer':
            return 2
        elif role == 'guest':
            return 3
        elif role == 'maintainer':
            return 4
        SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_ROLE_INVALID, self.interactive)

    @require_valid_token()
    def get_all_projects(self) -> list:
        api_url = f'{AppConfig.Connections.url_harbor}/api/v2.0/projects'
        headers = {'Authorization': 'Bearer ' + self.user.access_token}
        try:
            response = requests.get(api_url, headers=headers, verify=False)
            if response.status_code == 200:
                project_names = []
                for project in response.json():
                    project_names.append(project['name'])
                return project_names
            elif response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.ERROR_CONNECTION, self.interactive)
            elif response.status_code == 403:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_403, self.interactive)
            else:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_OTHER, self.interactive)
        except Exception:
            SrvErrorHandler.default_handle(response.content, self.interactive)

    @require_valid_token()
    def get_all_repos(self, project: str) -> list:
        api_url = f'{AppConfig.Connections.url_harbor}/api/v2.0/repositories'
        if project:
            api_url = f'{AppConfig.Connections.url_harbor}/api/v2.0/projects/{project}/repositories'
        headers = {'Authorization': 'Bearer ' + self.user.access_token}
        try:
            response = requests.get(api_url, headers=headers, verify=False)
            if response.status_code == 200:
                repo_names = []
                for repo in response.json():
                    repo_names.append(repo['name'])
                return repo_names
            elif response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.ERROR_CONNECTION, self.interactive)
            elif response.status_code == 403:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_403, self.interactive)
            else:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_OTHER, self.interactive)
        except Exception:
            SrvErrorHandler.default_handle(response.content, self.interactive)

    @require_valid_token(azp='harbor')
    def get_current_user_secret(self) -> str:
        api_url = f'{AppConfig.Connections.url_harbor}/api/v2.0/users/current'
        headers = {'Authorization': 'Bearer ' + self.user.access_token}
        try:
            response = requests.get(api_url, headers=headers, verify=False)
            if response.status_code == 200:
                return response.json()['oidc_user_meta']['secret']
            elif response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.ERROR_CONNECTION, self.interactive)
            elif response.status_code == 403:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_403, self.interactive)
            else:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_OTHER, self.interactive)
        except Exception:
            SrvErrorHandler.default_handle(response.content, self.interactive)

    @require_valid_token(azp='harbor')
    def create_project(self, name: str, visibility: str) -> bool:
        public = self.get_public(visibility)
        api_url = f'{AppConfig.Connections.url_harbor}/api/v2.0/projects'
        headers = {'Authorization': 'Bearer ' + self.user.access_token}
        payload = {
            'project_name': name,
            'public': public,
            'metadata': {
                'public': str(public).lower(),
                'enable_content_trust': 'false',
                'prevent_vul': 'false',
                'severity': 'none',
                'auto_scan': 'false',
                'reuse_sys_cve_allowlist': 'true',
                'retention_id': 'cli',
            },
            'registry_id': None,
            'storage_limit': 0,
        }
        try:
            response = requests.post(api_url, headers=headers, json=payload, verify=False)
            if response.status_code == 200 or response.status_code == 201:
                return True
            elif response.status_code == 401:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_401, self.interactive)
            elif response.status_code == 403:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_403, self.interactive)
            elif response.status_code == 404:
                SrvErrorHandler.customized_handle(ECustomizedError.ERROR_CONNECTION, self.interactive)
            elif response.status_code == 409:
                SrvErrorHandler.customized_handle(
                    ECustomizedError.CONTAINER_REGISTRY_DUPLICATE_PROJECT, self.interactive
                )
            else:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_OTHER, self.interactive)
        except Exception:
            SrvErrorHandler.default_handle(response.content, self.interactive)
        return False

    @require_valid_token(azp='harbor')
    def share_project(self, role: str, project: str, username: str) -> bool:
        api_url = f'{AppConfig.Connections.url_harbor}/api/v2.0/projects/{project}/members'
        role_number = self.get_role_number(role)
        headers = {'Authorization': 'Bearer ' + self.user.access_token}
        payload = {'role_id': role_number, 'member_user': {'username': username}}
        try:
            response = requests.post(api_url, headers=headers, json=payload, verify=False)
            if response.status_code == 200 or response.status_code == 201:
                return True
            elif response.status_code == 401:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_401, self.interactive)
            elif response.status_code == 403:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_403, self.interactive)
            elif response.status_code == 404:
                error_msg = loads(response.text)['errors'][0]['message']
                if username in error_msg:
                    SrvErrorHandler.customized_handle(ECustomizedError.USER_NOT_FOUND, self.interactive)
                else:
                    SrvErrorHandler.customized_handle(ECustomizedError.ERROR_CONNECTION, self.interactive)
            else:
                SrvErrorHandler.customized_handle(ECustomizedError.CONTAINER_REGISTRY_OTHER, self.interactive)
        except Exception:
            SrvErrorHandler.default_handle(response.content, self.interactive)
        return False
