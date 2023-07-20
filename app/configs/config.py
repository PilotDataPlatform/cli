# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

from functools import lru_cache
from pathlib import Path
from typing import Set

from pydantic import computed_field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='allow')

    project: str = 'pilot'
    app_name: str = 'pilotcli'

    @computed_field
    def config_path(self) -> str:
        return str(Path.home() / f'.{self.app_name}')

    config_file: str = 'config.ini'

    keycloak_device_client_id: str = 'cli'
    keycloak_api_key_audience: Set[str] = {'api-key'}

    vm_info: str = ''

    harbor_client_secret: str = ''
    url_harbor: str = ''

    domain: str = 'pilot.indocresearch.com'

    @computed_field
    def base_url(self) -> str:
        return f'https://api.{self.domain}/pilot'

    @computed_field
    def url_bff(self) -> str:
        return f'{self.base_url}/cli'

    @computed_field
    def url_keycloak_realm(self) -> str:
        return f'https://iam.{self.domain}/realms/pilot'

    @computed_field
    def url_keycloak(self) -> str:
        return f'{self.url_keycloak_realm}/protocol/openid-connect'

    @computed_field
    def url_authn(self) -> str:
        return f'{self.base_url}/portal/users/auth'

    @computed_field
    def url_refresh_token(self) -> str:
        return f'{self.base_url}/portal/users/refresh'

    @computed_field
    def url_file_tag(self) -> str:
        return f'{self.base_url}/portal/v2/%s/tags'

    @computed_field
    def url_upload_greenroom(self) -> str:
        return f'{self.base_url}/upload/gr'

    @computed_field
    def url_upload_core(self) -> str:
        return f'{self.base_url}/upload/core'

    @computed_field
    def url_status(self) -> str:
        return f'{self.base_url}/portal/v1/files/actions/tasks'

    @computed_field
    def url_download_greenroom(self) -> str:
        return f'{self.base_url}/portal/download/gr/'

    @computed_field
    def url_download_core(self) -> str:
        return f'{self.base_url}/portal/download/core/'

    @computed_field
    def url_v2_download_pre(self) -> str:
        return f'{self.url_bff}/v1/project/%s/files/download'

    @computed_field
    def url_dataset_v2download(self) -> str:
        return f'{self.base_url}/portal/download/core/v2/dataset'

    @computed_field
    def url_dataset(self) -> str:
        return f'{self.base_url}/portal/v1/dataset'

    @computed_field
    def url_validation(self) -> str:
        return f'{self.base_url}/v1/files/validation'


@lru_cache(1)
def get_settings() -> Settings:
    settings = Settings()
    return settings


ConfigClass = get_settings()
