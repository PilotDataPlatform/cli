# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import time
from multiprocessing.pool import ThreadPool

import pytest

from app.configs.app_config import AppConfig
from app.services.file_manager.file_download.download_client import SrvFileDownload
from app.services.file_manager.file_download.model import EFileStatus


def test_download_client_print_prepare_msg(capfd):
    msg = 'testing'

    pool = ThreadPool(2)
    download_client = SrvFileDownload('test_zone')
    async_fun = pool.apply_async(download_client.print_prepare_msg, (msg,))
    time.sleep(2)
    download_client.check_point = True

    # add the timeout to avoid the test stuck
    try:
        async_fun.get(timeout=5)
    except TimeoutError:
        raise AssertionError('prepare message not finished')

    pool.close()
    pool.join()

    out, _ = capfd.readouterr()
    assert msg in out
    assert msg.replace('ing', 'ed') in out


@pytest.mark.parametrize(
    'zone',
    [('greenroom'), ('core')],
)
def test_download_client_test_zone_download_url(zone):
    download_client = SrvFileDownload(zone)
    url = download_client.get_download_url()

    if zone == 'greenroom':
        assert url == AppConfig.Connections.url_download_greenroom
    else:
        assert url == AppConfig.Connections.url_download_core


def test_pre_download(fake_download_hash, httpx_mock, mocker):
    download_client = SrvFileDownload('test_zone')
    download_client.project_code = 'test_project'

    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)

    expect_status = 'WAITING'
    expect_file_path = 'test_file'
    hash_code, file_info = fake_download_hash
    httpx_mock.add_response(
        method='POST',
        url=AppConfig.Connections.url_v2_download_pre % (download_client.project_code),
        json={
            'code': 200,
            'error_msg': '',
            'page': 0,
            'total': 1,
            'num_of_pages': 1,
            'result': {
                'session_id': 'test_session',
                'target_names': [expect_file_path],
                'target_type': 'file',
                'container_code': download_client.project_code,
                'container_type': 'project',
                'action_type': 'data_download',
                'status': expect_status,
                'job_id': 'test_job',
                'payload': {'hash_code': hash_code, 'zone': 0},
            },
        },
    )

    status, file_path = download_client.pre_download()
    assert status == EFileStatus(expect_status)
    assert file_path == file_info.get('file_path')
