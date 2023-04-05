# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

import re
from multiprocessing import TimeoutError
from multiprocessing.pool import ThreadPool
from time import sleep

from app.configs.app_config import AppConfig
from app.services.file_manager.file_upload.models import FileObject
from app.services.file_manager.file_upload.upload_client import UploadClient


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


def test_resumable_pre_upload_success(httpx_mock, mocker):
    upload_client = UploadClient('test', 'project_code', 'parent_folder_id')
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    test_obj = FileObject('resumable_id', 'job_id', 'item_id', 'object/path', 'local_path', [])

    url = AppConfig.Connections.url_bff + f'/v1/project/{upload_client.project_code}/files/resumable'
    httpx_mock.add_response(
        method='POST', url=url, json={'result': [{'resumable_id': 'resumable_id', 'chunks_info': ['chunks_info']}]}
    )

    res = upload_client.resume_upload([test_obj])

    assert len(res) == 1
    assert res[0].resumable_id == 'resumable_id'
    assert res[0].uploaded_chunks == ['chunks_info']


def test_resumable_pre_upload_failed_with_404(httpx_mock, mocker):
    upload_client = UploadClient('test', 'project_code', 'parent_folder_id')
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    test_obj = FileObject('resumable_id', 'job_id', 'item_id', 'object/path', 'local_path', [])

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


def test_output_manifest_success(mocker):
    upload_client = UploadClient('test', 'project_code', 'parent_folder_id')
    json_dump_mocker = mocker.patch('json.dump', return_value=None)
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    test_obj = FileObject('resumable_id', 'job_id', 'item_id', 'object/path', 'local_path', [])

    res = upload_client.output_manifest([test_obj], 'test')

    assert res.get('project_code') == 'project_code'
    assert res.get('parent_folder_id') == 'parent_folder_id'
    assert len(res.get('file_objects')) == 1

    file_item = res.get('file_objects').get('item_id')
    assert file_item.get('resumable_id') == 'resumable_id'
    assert file_item.get('local_path') == 'local_path'
    assert file_item.get('object_path') == 'object/path'
    assert file_item.get('item_id') == 'item_id'

    json_dump_mocker.assert_called_once()
