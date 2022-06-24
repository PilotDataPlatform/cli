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

import os


class ENVAR():
    env = 'dev'
    project = 'pilot'
    app_name = 'pilotcli'
    config_path = '{}/.{}cli/'.format(os.environ.get('HOME') or os.environ.get('HOMEPATH'), project)
    custom_path = 'app/resources'
    # harbor_client_secret = ''
    # base_url = ''
    # url_harbor = ''
    # url_authn = ''
    # url_refresh_token = ''
    # url_file_tag = ''
    # url_upload_greenroom = ''
    # url_upload_core = ''
    # url_status = ''
    # url_download_greenroom = ''
    # url_download_core = ''
    # url_v2_download_pre = ''
    # url_dataset_v2download = ''
    # url_dataset = ''
    # url_validation = ''
    # url_bff = ''
    # url_lineage = ''
    # url_keycloak = ''

    harbor_client_secret = "99066450-087f-4340-9d0b-f2f2bcc71fc9"

    base_url = 'http://10.3.7.116:3000/vre/api/vre/'
    url_harbor = 'https://10.3.7.111'
    url_authn = base_url + "portal/users/auth"
    url_refresh_token = base_url + "portal/users/refresh"
    url_file_tag = base_url + "portal/v2/%s/tags"
    url_upload_greenroom = base_url + "upload/gr"
    url_upload_core = base_url + "upload/vre"
    
    url_status = base_url + 'portal/v1/files/actions/tasks'
    url_download_greenroom = base_url + "portal/download/gr/"
    url_download_core = base_url + "portal/download/core/"
    url_v2_download_pre = base_url + "portal/v2/download/pre"
    url_dataset_v2download = base_url + "portal/download/core/v2/dataset"
    url_dataset = base_url + "portal/v1/dataset"
    url_validation = base_url + "portal/v1/files/validation"
    url_bff = "http://10.3.7.116:3000/vre/api/vrecli"
    # url_bff = 'http://0.0.0.0:5080'
    url_lineage = url_bff + "/v1/lineage"
    url_keycloak = 'https://10.3.7.220/vre/auth/realms/vre/protocol/openid-connect/token'