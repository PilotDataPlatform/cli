# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from app.configs.app_config import AppConfig
from app.services.dataset_manager.dataset_download import SrvDatasetDownloadManager
from app.services.dataset_manager.model import EFileStatus


def test_dateset_pre_download_success(httpx_mock, mocker):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)

    httpx_mock.add_response(
        method='POST',
        url=AppConfig.Connections.url_dataset_v2download + '/download/pre',
        json={'result': {'payload': {'hash_code': 'hash_code'}, 'target_names': ['test.txt']}},
        status_code=200,
    )

    dataset_download_cliet = SrvDatasetDownloadManager('output_path', 'dataset_code', 'dataset_geid')

    res = dataset_download_cliet.pre_dataset_download()
    assert res.get('result').get('payload').get('hash_code') == 'hash_code'


def test_dateset_pre_download_status_waiting(httpx_mock, mocker):
    dataset_download_cliet = SrvDatasetDownloadManager('output_path', 'dataset_code', 'dataset_geid')

    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)

    httpx_mock.add_response(
        method='GET',
        url=AppConfig.Connections.url_download_core + f'v1/download/status/{dataset_download_cliet.hash_code}',
        json={'result': {'status': 'WAITING'}},
        status_code=200,
    )

    status = dataset_download_cliet.download_status()
    assert status == EFileStatus.WAITING


def test_dateset_pre_download_status_success(httpx_mock, mocker):
    dataset_download_cliet = SrvDatasetDownloadManager('output_path', 'dataset_code', 'dataset_geid')

    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)

    httpx_mock.add_response(
        method='GET',
        url=AppConfig.Connections.url_download_core + f'v1/download/status/{dataset_download_cliet.hash_code}',
        json={'result': {'status': 'SUCCEED'}},
        status_code=200,
    )

    status = dataset_download_cliet.download_status()
    assert status == EFileStatus.SUCCEED


def test_check_dateset_pre_download_status(httpx_mock, mocker):
    dataset_download_cliet = SrvDatasetDownloadManager('output_path', 'dataset_code', 'dataset_geid')

    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)

    httpx_mock.add_response(
        method='GET',
        url=AppConfig.Connections.url_download_core + f'v1/download/status/{dataset_download_cliet.hash_code}',
        json={'result': {'status': 'SUCCEED'}},
        status_code=200,
    )

    status = dataset_download_cliet.check_download_preparing_status()
    assert status == EFileStatus.SUCCEED


def test_avoid_duplicate_file_name_no_duplicate(mocker):
    dataset_download_cliet = SrvDatasetDownloadManager('output_path', 'dataset_code', 'dataset_geid')

    mocker.patch('os.path.isfile', side_effect=[False])
    file_name = dataset_download_cliet.avoid_duplicate_file_name('test.txt')

    assert file_name == 'test.txt'


def test_avoid_duplicate_file_name_duplicate_once(mocker):
    dataset_download_cliet = SrvDatasetDownloadManager('output_path', 'dataset_code', 'dataset_geid')

    mocker.patch('os.path.isfile', side_effect=[True, False])
    file_name = dataset_download_cliet.avoid_duplicate_file_name('test.txt')

    assert file_name == 'test (1).txt'


def test_download_dataset(httpx_mock, mocker):
    dataset_download_cliet = SrvDatasetDownloadManager('output_path', 'dataset_code', 'dataset_geid')

    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    mocker.patch(
        'app.services.dataset_manager.dataset_download.SrvDatasetDownloadManager.send_download_request',
        return_value='test.zip',
    )
    mocker.patch('os.path.isfile', return_value=True)
    success_msg = mocker.patch(
        'app.services.output_manager.message_handler.SrvOutPutHandler.download_success', return_value=None
    )

    httpx_mock.add_response(
        method='POST',
        url=AppConfig.Connections.url_dataset_v2download + '/download/pre',
        json={'result': {'payload': {'hash_code': 'hash_code'}, 'target_names': ['test.txt']}},
        status_code=200,
    )

    httpx_mock.add_response(
        method='GET',
        url=AppConfig.Connections.url_download_core + 'v1/download/status/hash_code',
        json={'result': {'status': 'SUCCEED'}},
        status_code=200,
    )

    dataset_download_cliet.download_dataset()
    success_msg.assert_called_once_with('test.zip')


def test_pre_dataset_version_download(httpx_mock, mocker):
    dataset_download_cliet = SrvDatasetDownloadManager('output_path', 'dataset_code', 'dataset_geid')

    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)

    httpx_mock.add_response(
        method='GET',
        url=AppConfig.Connections.url_dataset + f'/{dataset_download_cliet.dataset_geid}/download/pre?version=',
        json={'result': {'source': 'test.txt'}},
        status_code=200,
    )

    res = dataset_download_cliet.pre_dataset_version_download()
    assert res.get('result').get('source') == 'test.txt'


def test_download_dataset_version(httpx_mock, mocker):
    dataset_download_cliet = SrvDatasetDownloadManager('output_path', 'dataset_code', 'dataset_geid')

    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    mocker.patch(
        'app.services.dataset_manager.dataset_download.SrvDatasetDownloadManager.send_download_request',
        return_value='test.zip',
    )
    mocker.patch('os.path.isfile', return_value=True)
    success_msg = mocker.patch(
        'app.services.output_manager.message_handler.SrvOutPutHandler.download_success', return_value=None
    )

    httpx_mock.add_response(
        method='GET',
        url=AppConfig.Connections.url_dataset
        + f'/{dataset_download_cliet.dataset_geid}/download/pre?version=test_version',
        json={'result': {'source': 'test.txt'}},
        status_code=200,
    )

    dataset_download_cliet.download_dataset_version('test_version')
    success_msg.assert_called_once_with('test.zip')
