# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import base64
import hashlib
import math
import re
from functools import wraps
from multiprocessing import TimeoutError
from multiprocessing.pool import ThreadPool
from time import sleep

import click
import pytest

from app.configs.app_config import AppConfig
from app.services.file_manager.file_upload.exception import INVALID_CHUNK_ETAG
from app.services.file_manager.file_upload.models import FileObject
from app.services.file_manager.file_upload.upload_client import UploadClient
from tests.conftest import decoded_token


def mock_decorator(*args, **kwargs):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def test_check_status_success(httpx_mock, mocker):
    upload_client = UploadClient('project_code', 'parent_folder_id')

    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)

    httpx_mock.add_response(
        method='POST',
        url=AppConfig.Connections.url_bff + '/v1/query/geid',
        json={'result': [{'result': {'filename': 'test', 'status': 'ACTIVE'}}]},
        status_code=200,
    )

    test_obj = FileObject('test', 'test', 'test', 'test', 'test')
    result = upload_client.check_status(test_obj)

    assert result is True


def test_check_status_fail(httpx_mock, mocker):
    upload_client = UploadClient('project_code', 'parent_folder_id')

    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)

    httpx_mock.add_response(
        method='POST',
        url=AppConfig.Connections.url_bff + '/v1/query/geid',
        json={'result': [{'result': {'filename': 'test', 'status': 'REGISTERED'}}]},
        status_code=200,
    )

    test_obj = FileObject('test', 'test', 'test', 'test', 'test')
    result = upload_client.check_status(test_obj)

    assert result is False


def test_chunk_upload(httpx_mock, mocker):
    upload_client = UploadClient('project_code', 'parent_folder_id')

    test_presigned_url = 'http://test.url/presigned'
    url = re.compile('^' + AppConfig.Connections.url_upload_greenroom + '/v1/files/chunks/presigned.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': test_presigned_url})
    httpx_mock.add_response(method='PUT', url=test_presigned_url, json={'result': ''})
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))

    test_obj = FileObject('test', 'test', 'test', 'test', 'test')
    res = upload_client.upload_chunk(test_obj, 0, b'1', 'test_etag', 10)

    assert test_obj.progress_bar.n == 1
    assert res.status_code == 200


def test_chunk_upload_failed_with_401(httpx_mock, mocker):
    upload_client = UploadClient('project_code', 'parent_folder_id')

    test_presigned_url = 'http://test.url/presigned'
    url = re.compile('^' + AppConfig.Connections.url_upload_greenroom + '/v1/files/chunks/presigned.*$')
    httpx_mock.add_response(method='GET', url=url, json={'result': test_presigned_url})
    httpx_mock.add_response(method='PUT', url=test_presigned_url, json={'result': ''}, status_code=401)
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))

    test_obj = FileObject('test', 'test', 'test', 'test', 'test')
    with pytest.raises(SystemExit):
        upload_client.upload_chunk(test_obj, 0, b'1', 'test_etag', 10)


@pytest.mark.parametrize('total_size, chunk_size', [(101, 1), (101, 5), (101, 101)])
def test_stream_upload_success_with_new_upload(mocker, total_size, chunk_size):
    upload_client = UploadClient('project_code', 'parent_folder_id')
    upload_client.chunk_size = chunk_size
    test_data = '1' * total_size
    file_size = len(test_data)
    file_chunks = math.ceil(file_size / upload_client.chunk_size)
    file_local_path = 'test.txt'

    mocker.patch(
        'app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(file_size, file_chunks)
    )
    test_obj = FileObject('object_path', file_local_path)
    upload_chunk_mock = mocker.patch(
        'app.services.file_manager.file_upload.upload_client.UploadClient.upload_chunk', return_value=None
    )

    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        with open(file_local_path, 'w') as f:
            f.write(test_data)
        pool = ThreadPool(2)
        res = upload_client.stream_upload(test_obj, pool)

        pool.close()
        pool.join()

    assert len(res) == file_chunks
    # assert call with all chunks and params
    for i in range(file_chunks):
        chunk = test_data[i * upload_client.chunk_size : (i + 1) * upload_client.chunk_size].encode()

        etag = base64.b64encode(hashlib.md5(chunk).digest()).decode('utf-8')
        chunk_size = len(chunk)
        upload_chunk_mock.assert_any_call(test_obj, i + 1, chunk, etag, chunk_size)


@pytest.mark.parametrize('total_size, chunk_size, uploaded_offest', [(101, 1, 1), (101, 5, 1), (101, 101, 1)])
def test_stream_upload_success_with_resume_upload(mocker, total_size, chunk_size, uploaded_offest):
    upload_client = UploadClient('project_code', 'parent_folder_id')
    upload_client.chunk_size = chunk_size
    test_data = '1' * total_size
    file_size = len(test_data)
    file_chunks = math.ceil(file_size / upload_client.chunk_size)
    file_local_path = 'test.txt'
    uploaded_chunk, uploaded_offest = {}, uploaded_offest
    for i in range(uploaded_offest):
        chunk = test_data[i * upload_client.chunk_size : (i + 1) * upload_client.chunk_size].encode()
        etag = base64.b64encode(hashlib.md5(chunk).digest()).decode('utf-8')
        uploaded_chunk.update({str(i + 1): {'etag': etag, 'chunk_size': len(chunk)}})

    mocker.patch(
        'app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(file_size, file_chunks)
    )
    test_obj = FileObject('object_path', file_local_path)
    test_obj.uploaded_chunks = uploaded_chunk
    upload_chunk_mock = mocker.patch(
        'app.services.file_manager.file_upload.upload_client.UploadClient.upload_chunk', return_value=None
    )

    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        with open(file_local_path, 'w') as f:
            f.write(test_data)
        pool = ThreadPool(2)
        res = upload_client.stream_upload(test_obj, pool)

        pool.close()
        pool.join()

    assert len(res) == file_chunks - uploaded_offest
    # assert call with all chunks and params
    for i in range(file_chunks - uploaded_offest):
        offset = uploaded_offest + i
        chunk = test_data[offset * upload_client.chunk_size : (offset + 1) * upload_client.chunk_size].encode()

        etag = base64.b64encode(hashlib.md5(chunk).digest()).decode('utf-8')
        chunk_size = len(chunk)
        upload_chunk_mock.assert_any_call(test_obj, offset + 1, chunk, etag, chunk_size)


def test_stream_upload_failed_with_etag_mismatch(mocker):
    upload_client = UploadClient('project_code', 'parent_folder_id')
    upload_client.chunk_size = 2
    test_data = '1' * 10
    file_size = len(test_data)
    file_chunks = math.ceil(file_size / upload_client.chunk_size)
    file_local_path = 'test.txt'

    mocker.patch(
        'app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(file_size, file_chunks)
    )
    test_obj = FileObject('object_path', file_local_path)
    # wrong etag
    test_obj.uploaded_chunks = {'1': {'etag': 'test_etag', 'chunk_size': 2}}

    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        with open(file_local_path, 'w') as f:
            f.write(test_data)
        pool = ThreadPool(2)
        try:
            upload_client.stream_upload(test_obj, pool)
        except INVALID_CHUNK_ETAG as e:
            assert e.chunk_number == 1
        except Exception as e:
            raise AssertionError(f'Expect INVALID_CHUNK_ETAG but got {e}')

        finally:
            pool.close()
            pool.join()


def test_token_refresh_auto(mocker):
    AppConfig.Env.token_refresh_interval = 1

    token_refresh_mock = mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.refresh', return_value=None
    )

    upload_client = UploadClient('project_code', 'parent_folder_id')
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


def test_resumable_pre_upload_success(httpx_mock, mocker):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    upload_client = UploadClient('project_code', 'parent_folder_id')
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    test_obj = FileObject('object/path', 'local_path', 'resumable_id', 'job_id', 'item_id')

    url = AppConfig.Connections.url_bff + f'/v1/project/{upload_client.project_code}/files/resumable'
    httpx_mock.add_response(
        method='POST', url=url, json={'result': [{'resumable_id': 'resumable_id', 'chunks_info': ['chunks_info']}]}
    )

    res = upload_client.resume_upload([test_obj])

    assert len(res) == 1
    assert res[0].resumable_id == 'resumable_id'
    assert res[0].uploaded_chunks == ['chunks_info']


def test_resumable_pre_upload_failed_with_404(httpx_mock, mocker):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    upload_client = UploadClient('project_code', 'parent_folder_id')
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    test_obj = FileObject('object/path', 'local_path', 'resumable_id', 'job_id', 'item_id')

    url = AppConfig.Connections.url_bff + f'/v1/project/{upload_client.project_code}/files/resumable'
    httpx_mock.add_response(
        method='POST',
        url=url,
        json={'result': [{'resumable_id': 'resumable_id', 'chunks_info': ['chunks_info']}]},
        status_code=404,
    )

    try:
        upload_client.resume_upload([test_obj])
    except SystemExit:
        pass
    else:
        AssertionError('SystemExit not raised')


@pytest.mark.parametrize('case_insensitive', [True, False])
def test_check_upload_duplication_success(httpx_mock, mocker, case_insensitive):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    upload_client = UploadClient('project_code', 'parent_folder_id')
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    dup_obj = FileObject('object/duplicate', 'local_path', 'resumable_id', 'job_id', 'item_id')
    not_dup_object = FileObject('object/not_duplicate', 'local_path', 'resumable_id', 'job_id', 'item_id')

    url = AppConfig.Connections.url_base + '/portal/v1/files/exists'
    httpx_mock.add_response(
        method='POST',
        url=url,
        json={'result': [dup_obj.object_path.upper() if case_insensitive else dup_obj.object_path]},
    )

    not_dup_list, dup_list = upload_client.check_upload_duplication([dup_obj, not_dup_object])
    assert not_dup_list == [not_dup_object]
    assert dup_list == [dup_obj.object_path.upper() if case_insensitive else dup_obj.object_path]


def test_check_upload_duplication_fail_with_500(httpx_mock, mocker, capfd):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    upload_client = UploadClient('project_code', 'parent_folder_id')

    url = AppConfig.Connections.url_base + '/portal/v1/files/exists'
    httpx_mock.add_response(
        method='POST',
        url=url,
        json={'result': []},
        status_code=500,
    )

    try:
        upload_client.check_upload_duplication([])
    except SystemExit:
        out, _ = capfd.readouterr()

        expect = 'Error when checking file duplication\n'
        assert out == expect
    else:
        AssertionError('SystemExit not raised')


def test_output_manifest_success(mocker, tmp_path):
    upload_client = UploadClient('project_code', 'parent_folder_id')
    json_dump_mocker = mocker.patch('json.dump', return_value=None)
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    test_obj = FileObject('object/path', 'local_path', 'resumable_id', 'job_id', 'item_id')

    res = upload_client.output_manifest([test_obj], output_path=str(tmp_path / 'test'))

    assert res.get('project_code') == 'project_code'
    assert res.get('parent_folder_id') == 'parent_folder_id'
    assert len(res.get('file_objects')) == 1

    file_item = res.get('file_objects').get('item_id')
    assert file_item.get('resumable_id') == 'resumable_id'
    assert file_item.get('local_path') == 'local_path'
    assert file_item.get('object_path') == 'object/path'
    assert file_item.get('item_id') == 'item_id'

    json_dump_mocker.assert_called_once()
