import os

class ConfigClass(object):
    platform_user = {'username': 'jzhang21', 'password': 'testpassword'}
    project_contributor = {'username': 'jzhang33', 'password': 'testpassword'}
    project_collaborator = {'username': 'jzhang3', 'password': 'testpassword'}
    invalid_user = {'username': 'jzhang53', 'password': 'testpassword'}
    dataset_user = {'username': 'jzhang10', 'password': 'testpassword'}
    project_code = 'cli'
    dicom_project = "testproject"
    project_geid = "aa3775f8-0aba-4e38-a735-3fb983f8ec7b-1625673374"
    manifest_name = 'Manifest1'
    base_url = os.getenv("BASEURL")
    lineage_url = f"{base_url}/v1/lineage"
    file_info_url = f"{base_url}/v1/project/cli/file/exist"
    tear_down_url = f"{base_url}/v1/files/actions"
    content_url_raw = f"{base_url}/dataops/v1/archive"
