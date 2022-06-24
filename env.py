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
    url_harbor = ''
    url_authn = ''
    url_refresh_token = ''
    url_file_tag = ''
    url_upload_greenroom = ''
    url_upload_core = ''
    url_status = ''
    url_download_greenroom = ''
    url_download_core = ''
    url_v2_download_pre = ''
    url_dataset_v2download = ''
    url_dataset = ''
    url_validation = ''
    url_bff = ''
    url_lineage = ''
    url_keycloak = ''
