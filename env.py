import os

class ENVAR():
    env='dev'
    project = 'pilot'
    app_name = 'pilotcli'
    config_path = '{}/.{}cli/'.format(os.environ.get('HOME') or os.environ.get('HOMEPATH'), project)
    dicom_project = 'dicom_project_code'
    custom_path = 'app/resources'
    base_url = 'http://backend.url'
    service_url = 'http://service.url'
    url_harbor = 'https://harbor.url'
