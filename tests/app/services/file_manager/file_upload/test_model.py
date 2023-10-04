# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from app.configs.app_config import AppConfig
from app.services.file_manager.file_upload.models import FileObject


def test_file_upload_model_update_progress_bar(mocker):
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(100, 2))

    file_obj = FileObject('test', 'test', 'test', 'test', 'test')
    assert file_obj.progress_bar is not None

    file_obj.update_progress(50)
    assert file_obj.progress_bar.n == 50

    # progress bar should be closed when progress is 100%
    file_obj.update_progress(50)
    assert file_obj.progress_bar is None


def test_file_upload_model_close_progress_bar(mocker):
    mocker.patch('app.services.file_manager.file_upload.models.getsize', return_value=100)

    file_obj = FileObject('test', 'test', 'test', 'test', 'test')
    file_obj.close_progress()

    assert file_obj.progress_bar is None


def test_file_upload_model_generate_meta(mocker):
    AppConfig.Env.chunk_size = 10
    mocker.patch('app.services.file_manager.file_upload.models.getsize', return_value=100)

    file_obj = FileObject('test', 'test', 'test', 'test', 'test')
    total_size, total_chunks = file_obj.generate_meta('test')

    assert total_size == 100
    assert total_chunks == (100 / 10)
