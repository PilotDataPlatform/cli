# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from env import ConfigClass


class AppConfig(object):
    class Env(object):
        section = 'environment'
        project = ConfigClass.project
        user_config_path = ConfigClass.config_path
        msg_path = ConfigClass.custom_path
        user_config_file = f'{user_config_path}/config.ini'
        token_warn_need_refresh = 250
        token_refresh_interval = 120

        chunk_size = 1024 * 1024 * 20  # MB
        resilient_retry = 3
        resilient_backoff = 1
        resilient_retry_interval = 1
        resilient_retry_code = [502, 503, 504, 404, 401]
        pipeline_straight_upload = f'{project}cli_upload'
        default_upload_message = f'{project}cli straight uploaded'
        session_duration = 3600.0
        upload_batch_size = 100
        harbor_client_secret = ConfigClass.harbor_client_secret
        core_zone = 'core'
        green_zone = 'greenroom'
        core_bucket_prefix = 'core'
        greenroom_bucket_prefix = 'gr'

        keycloak_device_client_id = ConfigClass.keycloak_device_client_id

    class Connections(object):
        section = 'connections'
        url_harbor = ConfigClass.url_harbor
        url_authn = ConfigClass.url_authn
        url_refresh_token = ConfigClass.url_refresh_token
        url_file_tag = ConfigClass.url_file_tag
        url_upload_greenroom = ConfigClass.url_upload_greenroom
        url_upload_core = ConfigClass.url_upload_core
        url_status = ConfigClass.url_status
        url_lineage = ConfigClass.url_lineage
        url_download_greenroom = ConfigClass.url_download_greenroom
        url_download_core = ConfigClass.url_download_core
        url_v2_download_pre = ConfigClass.url_v2_download_pre
        url_dataset_v2download = ConfigClass.url_dataset_v2download
        url_dataset = ConfigClass.url_dataset
        url_validation = ConfigClass.url_validation
        url_keycloak = ConfigClass.url_keycloak
        url_keycloak_token = f'{ConfigClass.url_keycloak}/token'
        url_bff = ConfigClass.url_bff
        url_base = ConfigClass.base_url
