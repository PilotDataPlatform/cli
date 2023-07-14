# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

from app.configs.config import ConfigClass


class AppConfig:
    class Env:
        token_warn_need_refresh = 120  # refresh token if token is about to expire
        token_refresh_interval = 90  # auto refresh token every 40 seconds

        # NOTE: there is a limitation on minio that
        # the multipart number is 10000. so we set
        # the chunk_size as 20MB -> total 200GB
        chunk_size = 1024 * 1024 * 20  # MB
        resilient_retry = 3
        resilient_backoff = 1
        resilient_retry_interval = 1  # seconds
        resilient_retry_code = [502, 503, 504, 404, 401]
        pipeline_straight_upload = f'{ConfigClass.project}cli_upload'
        default_upload_message = f'{ConfigClass.project}cli straight uploaded'
        session_duration = 3600.0
        upload_batch_size = 100
        core_zone = 'core'
        green_zone = 'greenroom'
        core_bucket_prefix = 'core'
        greenroom_bucket_prefix = 'gr'

    class Connections:
        url_harbor = ConfigClass.url_harbor
        url_authn = ConfigClass.url_authn
        url_refresh_token = ConfigClass.url_refresh_token
        url_file_tag = ConfigClass.url_file_tag
        url_upload_greenroom = ConfigClass.url_upload_greenroom
        url_upload_core = ConfigClass.url_upload_core
        url_status = ConfigClass.url_status
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
