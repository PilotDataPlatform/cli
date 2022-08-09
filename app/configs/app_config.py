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
        chunk_size = 5  # chunk size mb
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
        url_harbor = ENVAR.url_harbor
        url_authn = ENVAR.url_authn
        url_refresh_token = ENVAR.url_refresh_token
        url_file_tag = ENVAR.url_file_tag
        url_upload_greenroom = ENVAR.url_upload_greenroom
        url_upload_core = ENVAR.url_upload_core
        url_status = ENVAR.url_status
        url_lineage = ENVAR.url_lineage
        url_download_greenroom = ENVAR.url_download_greenroom
        url_download_core = ENVAR.url_download_core
        url_v2_download_pre = ENVAR.url_v2_download_pre
        url_dataset_v2download = ENVAR.url_dataset_v2download
        url_dataset = ENVAR.url_dataset
        url_validation = ENVAR.url_validation
        url_keycloak = ENVAR.url_keycloak
        url_bff = ENVAR.url_bff
