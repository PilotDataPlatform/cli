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

from env import ENVAR


class AppConfig(object):

    class Env(object):
        section = "environment"
        project = ENVAR.project
        user_config_path = ENVAR.config_path
        msg_path = ENVAR.custom_path
        user_config_file = f"{user_config_path}/config.ini"
        token_warn_need_refresh = 120  # seconds
        chunk_size = 2  # chunk size mb
        resilient_retry = 3
        resilient_backoff = 1
        resilient_retry_code = [502, 503, 504, 404, 401]
        pipeline_straight_upload = f"{project}cli_upload"
        default_upload_message = f"{project}cli straight uploaded"
        session_duration = 3600.0
        harbor_client_secret = ENVAR.harbor_client_secret
        core_zone = 'core'
        green_zone = 'greenroom'

    class Connections(object):
        section = "connections"
        base_url = ENVAR.base_url
        service_url = ENVAR.service_url
        keycloak_url = ENVAR.keycloak_url
        url_harbor = ENVAR.url_harbor
        url_authn = base_url + "portal/users/auth"
        url_refresh_token = base_url + "portal/users/refresh"
        url_file_tag = base_url + "portal/dataops/v2/containers/"
        url_upload_greenroom = base_url + "upload/gr"
        url_upload_core = base_url + "upload/vre"
        url_download_greenroom = base_url + "portal/download/gr/"
        url_download_core = base_url + "portal/download/core/"
        url_v2_download_pre = base_url + "portal/v2/download/pre"
        url_dataset_v2download = base_url + "portal/download/core/v2/dataset"
        url_dataset = base_url + "portal/v1/dataset"
        url_validation = base_url + "portal/v1/files/validation"
        # url_bff = service_url + "api/vrecli"
        url_bff = 'http://0.0.0.0:5080'
        url_keycloak = keycloak_url + "auth/realms/vre/protocol/openid-connect/token"
