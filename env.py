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
    base_url = 'http://10.3.7.116:3000/***REMOVED***/api/***REMOVED***/'
    service_url = 'http://10.3.7.116:3000/***REMOVED***/'
    keycloak_url = 'https://10.3.7.220/***REMOVED***/'
    url_harbor = 'https://10.3.7.111'
    harbor_client_secret = "99066450-087f-4340-9d0b-f2f2bcc71fc9"
