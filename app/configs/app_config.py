# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from env import ConfigClass


class AppConfig(object):
    class Env(object):
        section = 'environment'
        project = ConfigClass.project
        user_config_path = ConfigClass.config_path
        msg_path = ConfigClass.custom_path
        user_config_file = f'{user_config_path}/config.ini'
        token_warn_need_refresh = 120  # seconds
        chunk_size = 1024 * 1024 * 5  # chunk size 5mb
        resilient_retry = 3
        resilient_backoff = 1
        resilient_retry_interval = 1  # seconds
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
        url_bff = ConfigClass.url_bff
        # add url_base to check if value exist
        url_base = ConfigClass.base_url
