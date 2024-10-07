# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import os

from dotenv import load_dotenv
from pydantic import BaseSettings
from pydantic import Extra

load_dotenv()
load_dotenv('/etc/environment')


class Settings(BaseSettings):
    env = 'dev'
    project = 'pilot'
    app_name = 'pilotcli'
    config_path = '{}/.{}cli/'.format(os.environ.get('HOME') or os.environ.get('HOMEPATH'), project)
    custom_path = 'app/resources'
    harbor_client_secret: str = ''
    base_url: str = ''
    url_harbor: str = ''
    url_bff: str = ''
    url_keycloak: str = ''

    keycloak_device_client_id: str = 'cli_test2'

    VM_INFO: str = ''

    def modify_values(self, settings):
        settings.url_authn = settings.base_url + 'portal/users/auth'
        settings.url_refresh_token = settings.base_url + 'portal/users/refresh'
        settings.url_file_tag = settings.base_url + 'portal/v2/%s/tags'
        settings.url_upload_greenroom = settings.base_url + 'upload/gr'
        settings.url_upload_core = settings.base_url + 'upload/core'
        settings.url_status = settings.base_url + 'portal/v1/files/actions/tasks'
        settings.url_download_greenroom = settings.base_url + 'portal/download/gr/'
        settings.url_download_core = settings.base_url + 'portal/download/core/'
        settings.url_v2_download_pre = settings.url_bff + '/v1/project/%s/files/download'
        settings.url_dataset_v2download = settings.base_url + 'portal/download/core/v2/dataset'
        settings.url_dataset = settings.base_url + 'portal/v1/dataset'
        settings.url_validation = settings.base_url + 'v1/files/validation'
        settings.url_lineage = settings.url_bff + '/v1/lineage'

        return settings

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = Extra.allow

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                env_settings,
                init_settings,
                file_secret_settings,
            )


def get_settings():
    settings = Settings()
    settings = settings.modify_values(settings)
    return settings


ConfigClass = get_settings()
