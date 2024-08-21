# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import click
import jwt
import pytest
from pytest_httpx import IteratorStream

from app.configs.app_config import AppConfig
from app.models.item import ItemZone
from app.services.file_manager.file_download.download_client import SrvFileDownload
from app.services.file_manager.file_download.model import EFileStatus
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import customized_error_msg
from tests.conftest import decoded_token


@pytest.mark.parametrize('file_status', [EFileStatus.SUCCEED, EFileStatus.FAILED, EFileStatus.WAITING])
def test_file_download_client_prepare_download_success(mocker, httpx_mock, file_status: EFileStatus):
    test_file_path = 'test_file_path'
    hash_token = jwt.encode({'file_path': test_file_path}, key='unittest')

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    download_client = SrvFileDownload(0, False)
    download_client.file_geid = ['test']
    download_client.project_code = 'test_project'

    httpx_mock.add_response(
        url=f'http://bff_cli/v1/project/{download_client.project_code}/files/download',
        method='POST',
        status_code=200,
        json={
            'result': {
                'payload': {
                    'hash_code': hash_token,
                },
                'status': file_status.value,
            }
        },
    )

    pre_status, file_path = download_client.prepare_download()
    assert pre_status == file_status
    assert file_path == test_file_path


@pytest.mark.parametrize(
    'status_code',
    [
        403,
        400,
        500,
    ],
)
def test_file_download_client_prepare_download_failed(mocker, httpx_mock, capfd, status_code: int):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    download_client = SrvFileDownload(0, True)
    download_client.file_geid = ['test']
    download_client.project_code = 'test_project'

    httpx_mock.add_response(
        url=f'http://bff_cli/v1/project/{download_client.project_code}/files/download',
        method='POST',
        status_code=status_code,
        json={'error_msg': 'number of file must greater than 0'},
    )

    try:
        download_client.pre_download()
    except SystemExit:
        out, _ = capfd.readouterr()

        expect = {
            500: ECustomizedError.DOWNLOAD_FAIL,
            403: ECustomizedError.NO_FILE_PERMMISION,
            400: ECustomizedError.FOLDER_EMPTY,
        }
        assert out == customized_error_msg(expect.get(status_code)) + '\n'
    else:
        AssertionError('SystemExit not raised')


@pytest.mark.parametrize(
    'zone',
    [
        ItemZone.GREENROOM.value,
        ItemZone.CORE.value,
    ],
)
def test_file_download_url_based_on_different_zones(zone: str):
    download_client = SrvFileDownload(0, True)
    download_client.file_geid = ['test']
    download_client.project_code = 'test_project'

    url = download_client.get_download_url(zone)
    except_url = {
        ItemZone.GREENROOM.value: AppConfig.Connections.url_download_greenroom,
        ItemZone.CORE.value: AppConfig.Connections.url_download_core,
    }.get(zone)

    assert url == except_url


@pytest.mark.parametrize(
    'total_size_presented',
    [True, False],
)
def test_file_stream_download(mocker, httpx_mock, total_size_presented):
    file_url = 'http://test.com'
    file_content = b'123'

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    httpx_mock.add_response(
        url=file_url,
        method='GET',
        status_code=200,
        content=IteratorStream([file_content]),
    )

    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        download_client = SrvFileDownload(0, True)
        download_client.file_geid = ['test']
        download_client.project_code = 'test_project'
        download_client.total_size = len(file_content) if total_size_presented else None

        download_client.download_file(file_url, 'test_file')

        with open('test_file', 'r') as f:
            assert f.read() == '123'


@pytest.mark.parametrize(
    'total_size',
    [1, 5],
)
def test_file_stream_download_failed_with_invalid_size(mocker, httpx_mock, capsys, total_size):
    file_url = 'http://test.com'
    file_content = b'123'

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    httpx_mock.add_response(
        url=file_url,
        method='GET',
        status_code=200,
        content=IteratorStream([file_content]),
    )

    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        download_client = SrvFileDownload(0, True)
        download_client.file_geid = ['test']
        download_client.project_code = 'test_project'
        download_client.total_size = total_size

        with pytest.raises(SystemExit):
            download_client.download_file(file_url, 'test_file')

        out, _ = capsys.readouterr()
        out = out.split('\n')
        assert out[1] == customized_error_msg(ECustomizedError.DOWNLOAD_SIZE_MISMATCH) % (total_size, len(file_content))


@pytest.mark.parametrize(
    'zone',
    [
        ItemZone.GREENROOM.value,
        ItemZone.CORE.value,
    ],
)
def test_download_url(zone):
    test_client = SrvFileDownload(zone, True)

    except_url = {
        ItemZone.GREENROOM.value: AppConfig.Connections.url_download_greenroom,
        ItemZone.CORE.value: AppConfig.Connections.url_download_core,
    }.get(zone)

    assert test_client.get_download_url(zone) == except_url


@pytest.mark.parametrize(
    'zone',
    [
        ItemZone.GREENROOM.value,
        ItemZone.CORE.value,
    ],
)
def test_simple_download_with_file(mocker, zone):
    test_client = SrvFileDownload(zone, True)

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    handle_geid_downloading_mock = mocker.patch(
        'app.services.file_manager.file_download.download_client.SrvFileDownload.handle_geid_downloading',
        return_value=(True, 'test_file'),
    )
    predownload_mock = mocker.patch(
        'app.services.file_manager.file_download.download_client.SrvFileDownload.pre_download',
        return_value=(EFileStatus.SUCCEED, 'http://presigned_url'),
    )

    download_mock = mocker.patch(
        'app.services.file_manager.file_download.download_client.SrvFileDownload.download_file',
    )

    with click.testing.CliRunner().isolated_filesystem():
        test_client.simple_download_file('./', [{'id': 'test_id'}])

    handle_geid_downloading_mock.assert_called_once()
    predownload_mock.assert_called_once()
    download_mock.assert_called_once_with('http://presigned_url', './test_file')


@pytest.mark.parametrize(
    'zone',
    [
        ItemZone.GREENROOM.value,
        ItemZone.CORE.value,
    ],
)
def test_simple_download_with_folder(mocker, zone):
    test_client = SrvFileDownload(zone, True)
    test_client.hash_code = 'test_hash_code'

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    handle_geid_downloading_mock = mocker.patch(
        'app.services.file_manager.file_download.download_client.SrvFileDownload.handle_geid_downloading',
        return_value=(False, 'test_file'),
    )
    predownload_mock = mocker.patch(
        'app.services.file_manager.file_download.download_client.SrvFileDownload.pre_download',
        return_value=(EFileStatus.SUCCEED, 'download_url'),
    )

    status_check_mock = mocker.patch(
        'app.services.file_manager.file_download.download_client.SrvFileDownload.check_download_preparing_status',
        return_value=EFileStatus.SUCCEED,
    )

    download_mock = mocker.patch(
        'app.services.file_manager.file_download.download_client.SrvFileDownload.download_file',
    )

    download_service_url = {
        ItemZone.GREENROOM.value: AppConfig.Connections.url_download_greenroom,
        ItemZone.CORE.value: AppConfig.Connections.url_download_core,
    }.get(zone)
    with click.testing.CliRunner().isolated_filesystem():
        test_client.simple_download_file('./', [{'id': 'test_id'}])

    handle_geid_downloading_mock.assert_called_once()
    predownload_mock.assert_called_once()
    status_check_mock.assert_called_once()
    download_mock.assert_called_once_with(f'{download_service_url}/v1/download/{test_client.hash_code}', './test_file')
