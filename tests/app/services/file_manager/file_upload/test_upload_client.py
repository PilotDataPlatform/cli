# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

from functools import wraps
import re
from multiprocessing import TimeoutError
from multiprocessing.pool import ThreadPool
from time import sleep

from app.configs.app_config import AppConfig
from app.services.file_manager.file_upload.models import FileObject
from app.services.file_manager.file_upload.upload_client import UploadClient


def mock_decorator(*args, **kwargs):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def test_check_status_success(httpx_mock, mocker):
    upload_client = UploadClient('test', 'test', 'test')

    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)

    httpx_mock.add_response(
        method='POST',
        url=AppConfig.Connections.url_bff + '/v1/query/geid',
        json={'result': [{'result': {'filename': 'test', 'status': 'ACTIVE'}}]},
        status_code=200,
    )

    test_obj = FileObject('test', 'test', 'test', 'test', 'test', [])
    result = upload_client.check_status(test_obj)

    assert result is True


def test_check_status_fail(httpx_mock, mocker):
    upload_client = UploadClient('test', 'test', 'test')

    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)

    httpx_mock.add_response(
        method='POST',
        url=AppConfig.Connections.url_bff + '/v1/query/geid',
        json={'result': [{'result': {'filename': 'test', 'status': 'REGISTERED'}}]},
        status_code=200,
    )

    test_obj = FileObject('test', 'test', 'test', 'test', 'test', [])
    result = upload_client.check_status(test_obj)

    assert result is False
=======
def test_chunk_upload(httpx_mock, mocker):
    upload_client = UploadClient('test', 'test', 'test')

    test_presigned_url = 'http://test/presigned'
    url = re.compile('^' + upload_client.base_url + '/v1/files/chunks/presigned.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': test_presigned_url})
    httpx_mock.add_response(method='PUT', url=test_presigned_url, json={'result': ''})
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))

    test_obj = FileObject('test', 'test', 'test', 'test', 'test', [])
    res = upload_client.upload_chunk(test_obj, 0, b'1')

    assert test_obj.progress_bar.n == 1
    assert res.status_code == 200


def test_token_refresh_auto(mocker):
    AppConfig.Env.token_refresh_interval = 1

    token_refresh_mock = mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.refresh', return_value=None
    )

    upload_client = UploadClient('test', 'test', 'test')
    pool = ThreadPool(2)
    async_fun = pool.apply_async(upload_client.upload_token_refresh)
    sleep(3)
    upload_client.set_finish_upload()

    # add the timeout to avoid the test stuck
    try:
        async_fun.get(timeout=5)
    except TimeoutError:
        raise AssertionError('token refresh failed')

    pool.close()
    pool.join()

    # make sure the token refresh function is called
    token_refresh_mock.assert_called_once()
