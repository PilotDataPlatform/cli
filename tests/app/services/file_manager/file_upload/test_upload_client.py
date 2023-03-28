# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

import re

from tqdm import tqdm

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
    test_bar = tqdm(total=1, unit='B', unit_scale=True, desc='test', leave=True)
    upload_client.upload_chunk(test_obj, 0, b'', test_bar)
