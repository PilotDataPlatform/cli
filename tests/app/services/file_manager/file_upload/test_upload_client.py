# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

from functools import wraps

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
