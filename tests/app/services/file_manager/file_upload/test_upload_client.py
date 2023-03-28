# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

from multiprocessing.pool import ThreadPool

from app.configs.app_config import AppConfig
from app.services.file_manager.file_upload.upload_client import UploadClient


def test_token_refresh_auto(mocker):
    AppConfig.Env.token_refresh_interval = 1

    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.refresh', return_value=None)

    upload_client = UploadClient('test', 'test', 'test')
    pool = ThreadPool(2)
    async_fun = pool.apply_async(upload_client.upload_token_refresh)
    upload_client.set_finish_upload()

    # add the timeout to avoid the test stuck
    try:
        async_fun.get(timeout=5)
    except BaseException:
        AssertionError('token refresh failed')

    pool.close()
    pool.join()
