# Copyright (C) 2022-2026 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pytest

from app.configs.app_config import AppConfig
from app.models.item import ItemType
from app.utils.aggregated import (
    check_item_duplication,
    get_latest_cli_version,
    get_version_compatibility,
    identify_target_folder,
    normalize_input_paths,
    normalize_join,
    search_item,
    validate_folder_name,
)
from tests.conftest import decoded_token

test_project_code = 'testproject'


def test_search_file_should_return_200(httpx_mock, mocker):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    httpx_mock.add_response(
        method='GET',
        url=f'http://bff_cli/v1/project/{test_project_code}/search?zone=zone&'
        f'project_code={test_project_code}&path=folder_relative_path&container_type=project'
        '&status=ACTIVE',
        json={
            'code': 200,
            'error_msg': '',
            'result': {
                'id': 'file-id',
                'parent': 'parent-id',
                'parent_path': 'folder1',
                'restore_path': None,
                'status': 'ACTIVE',
                'type': 'file',
                'zone': 0,
                'name': 'test-file',
                'size': 1048576,
                'owner': 'admin',
                'container_code': test_project_code,
                'container_type': 'project',
                'created_time': '2021-07-02 16:34:09.164000',
                'last_updated_time': '2021-07-02 16:34:09.164000',
                'storage': {'id': 'storage-id', 'location_uri': 'minio-path', 'version': 'version-id'},
                'extended': {'id': 'extended-id', 'extra': {'tags': [], 'system_tags': [], 'attributes': {}}},
            },
        },
        status_code=200,
    )
    expected_result = {
        'id': 'file-id',
        'parent': 'parent-id',
        'parent_path': 'folder1',
        'restore_path': None,
        'status': 'ACTIVE',
        'type': 'file',
        'zone': 0,
        'name': 'test-file',
        'size': 1048576,
        'owner': 'admin',
        'container_code': test_project_code,
        'container_type': 'project',
        'created_time': '2021-07-02 16:34:09.164000',
        'last_updated_time': '2021-07-02 16:34:09.164000',
        'storage': {'id': 'storage-id', 'location_uri': 'minio-path', 'version': 'version-id'},
        'extended': {'id': 'extended-id', 'extra': {'tags': [], 'system_tags': [], 'attributes': {}}},
    }
    res = search_item(test_project_code, 'zone', 'folder_relative_path', 'project')
    assert res['result'] == expected_result


def test_search_item_returns_response_when_status_code_is_404(httpx_mock, mocker, fake):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    expected_response = {'result': {'id': fake.uuid4()}}

    httpx_mock.add_response(
        method='GET',
        url=f'http://bff_cli/v1/project/{test_project_code}/search?zone=zone&'
        f'project_code={test_project_code}&path=folder_relative_path&container_type=project'
        '&status=ACTIVE',
        json=expected_response,
        status_code=404,
    )

    response = search_item(test_project_code, 'zone', 'folder_relative_path', 'project')

    assert response == expected_response


def test_search_file_error_handling_with_403(httpx_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    httpx_mock.add_response(
        method='GET',
        url=f'http://bff_cli/v1/project/{test_project_code}/search?zone=zone&'
        f'project_code={test_project_code}&path=folder_relative_path&container_type=project'
        '&status=ACTIVE',
        json={},
        status_code=403,
    )
    with pytest.raises(SystemExit):
        search_item(test_project_code, 'zone', 'folder_relative_path', 'project')
    out, _ = capsys.readouterr()
    assert (
        out.rstrip()
        == 'Permission denied. Please verify your role in the Project has permission to perform this action.'
    )


def test_search_file_error_handling_with_401(httpx_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    mocker.patch('app.services.user_authentication.token_manager.login_using_api_key', return_value=True)
    httpx_mock.add_response(
        method='GET',
        url=f'http://bff_cli/v1/project/{test_project_code}/search?zone=zone&'
        f'project_code={test_project_code}&path=folder_relative_path&container_type=project'
        '&status=ACTIVE',
        text='Authentication failed.',
        status_code=401,
    )
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.refresh', return_value=None)

    with pytest.raises(SystemExit):
        search_item(test_project_code, 'zone', 'folder_relative_path', 'project')
    out, _ = capsys.readouterr()
    assert out.rstrip() == 'Your login session has expired. Please try again or log in again.'


def test_check_duplicate_fail_with_error_code(httpx_mock, mocker, capsys):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    httpx_mock.add_response(
        url=AppConfig.Connections.url_base + '/portal/v1/files/exists',
        method='POST',
        json={'error': 'internal server error'},
        status_code=500,
    )

    with pytest.raises(SystemExit):
        check_item_duplication(['test_path'], 0, 'test_project_code')
    out, _ = capsys.readouterr()
    assert out.rstrip() == '{"error": "internal server error"}'


@pytest.mark.parametrize('folder_name', ['/:?.\\*<>|”\'', ''.join(['1' for _ in range(101)])])
def test_validate_folder_name(folder_name):
    valid = validate_folder_name(folder_name)
    assert valid is False


@pytest.mark.parametrize(
    'input_path,expected_result',
    [
        (
            f'project_code/{ItemType.NAMEFOLDER.get_prefix_by_type()}username',
            ('project_code', ItemType.NAMEFOLDER, 'username'),
        ),
        (
            f'project_code/{ItemType.NAMEFOLDER.get_prefix_by_type()}username/folder1',
            ('project_code', ItemType.NAMEFOLDER, 'username/folder1'),
        ),
        (
            f'project_code/{ItemType.SHAREDFOLDER.get_prefix_by_type()}folder1',
            ('project_code', ItemType.SHAREDFOLDER, 'folder1'),
        ),
        (
            f'project_code/{ItemType.SHAREDFOLDER.get_prefix_by_type()}folder1/folder2',
            ('project_code', ItemType.SHAREDFOLDER, 'folder1/folder2'),
        ),
    ],
)
def test_identify_target_folder_success_with_different_path(mocker, input_path, expected_result):
    mocker.patch('app.utils.aggregated.validate_folder_name', return_value=True)
    result = identify_target_folder(input_path)
    assert result == expected_result


def test_identify_target_folder_fail_with_invalid_input(mocker):
    mocker.patch('app.utils.aggregated.validate_folder_name', return_value=False)
    with pytest.raises(SystemExit):
        identify_target_folder('project_code')


def test_normalize_input_paths():
    @normalize_input_paths(['str_input', 'tuple_input'])
    def test_func(str_input, tuple_input):
        return str_input, tuple_input

    result = test_func(str_input='project_code\\folder1', tuple_input=('.\\folder2\\test.txt', '.\\folder3\\test2.txt'))
    assert result == ('project_code/folder1', ('./folder2/test.txt', './folder3/test2.txt'))


def test_normalize_join():
    # linux path, windows path
    input_paths = ['project_code\\folder1', 'folder2\\test.txt']
    expected_result = 'project_code/folder1/folder2/test.txt'
    result = normalize_join(input_paths[0], input_paths[1])
    assert result == expected_result


def test_get_version_compatibility_pass(httpx_mock):
    httpx_mock.add_response(
        url=AppConfig.Connections.url_bff + '/public/v1/validate/cli/version?version=1.0.0',
        method='GET',
        json={
            'result': {
                'minimum_cli_version': '1.0.0',
                'minimum_server_version': '1.0.0',
            }
        },
        status_code=200,
    )
    get_version_compatibility('1.0.0')


def test_get_version_compatibility_fail_with_version_not_found(httpx_mock, capsys):
    httpx_mock.add_response(
        url=AppConfig.Connections.url_bff + '/public/v1/validate/cli/version?version=1.0.0',
        method='GET',
        json={'result': {}},
        status_code=200,
    )
    with pytest.raises(SystemExit):
        get_version_compatibility('1.0.0')
    out, _ = capsys.readouterr()
    assert 'CLI version is not found. Please use the correct cli version.' in out.rstrip()


def test_get_version_compatibility_fail_with_version_incompatible(httpx_mock, capsys):
    min_cli_version = '1.1.0'
    min_server_version = '1.2.0'
    httpx_mock.add_response(
        url=AppConfig.Connections.url_bff + '/public/v1/validate/cli/version?version=1.0.0',
        method='GET',
        json={
            'result': {
                'minimum_cli_version': min_cli_version,
                'minimum_server_version': min_server_version,
            }
        },
        status_code=200,
    )
    with pytest.raises(SystemExit):
        get_version_compatibility('1.0.0')
    out, _ = capsys.readouterr()
    assert (
        f'CLI version is incompatible with server version. Please update the CLI to version {min_cli_version}'
        + f' or later, and minimum server version is {min_server_version}.'
    ) in out.rstrip()


@pytest.mark.parametrize('platform_name', ['Linux', 'Windows', 'Darwin'])
def test_get_download_link_by_platform(mocker, platform_name, httpx_mock):
    mocker.patch('app.utils.aggregated.platform.system', return_value=platform_name)
    expected_result = {
        'linux': {
            'version': '1.0.0',
            'download_url': 'https://example.com/download/linux',
        },
        'windows': {
            'version': '1.0.1',
            'download_url': 'https://example.com/download/windows',
        },
        'macos': {
            'version': '1.1.0',
            'download_url': 'https://example.com/download/macos',
        },
    }
    httpx_mock.add_response(
        url=AppConfig.Connections.url_fileops_greenroom + '/v1/download/cli/presigned',
        method='GET',
        json={'result': expected_result},
        status_code=200,
    )

    version, url = get_latest_cli_version()
    if platform_name.lower() == 'darwin':
        platform_name = 'macos'
    assert str(version) == expected_result[platform_name.lower()]['version']
    assert url == expected_result[platform_name.lower()]['download_url']
