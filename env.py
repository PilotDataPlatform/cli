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
    harbor_client_secret = ''
    
    base_url = ''
    url_bff = ''
    url_harbor = ''
    url_authn = base_url + ''
    url_refresh_token = base_url + ''
    url_file_tag = base_url + ''
    url_upload_greenroom = base_url + ''
    url_upload_core = base_url + ''
    url_download_greenroom = base_url + ''
    url_download_core = base_url + ''
    url_v2_download_pre = base_url + ''
    url_dataset_v2download = base_url + ''
    url_dataset = base_url + ''
    url_validation = base_url + ''
    url_keycloak = ''
