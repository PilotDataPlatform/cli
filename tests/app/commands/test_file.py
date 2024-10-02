# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import click

from app.commands.file import file_put
from app.commands.file import file_resume
from app.services.file_manager.file_upload.models import FileObject
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import customized_error_msg


def test_file_upload_command_success_with_attribute(mocker, cli_runner):
    project_code = 'test_project'
    target_folder = 'admin'

    mocker.patch('app.commands.file.identify_target_folder', return_value=(project_code, target_folder))
    mocker.patch('app.commands.file.validate_upload_event', return_value={'source_file': '', 'attribute': 'test'})
    mocker.patch('app.commands.file.assemble_path', return_value=('test', {'id': 'id'}, True, 'test'))

    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    test_obj = FileObject('resumable_id', 'job_id', 'item_id', 'object/path', 'local_path')

    simple_upload_mock = mocker.patch('app.commands.file.simple_upload', return_value=[test_obj])
    attribute_mock = mocker.patch(
        'app.services.file_manager.file_manifests.SrvFileManifests.attach_manifest', return_value=None
    )

    # create a test file
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        with open('test.txt', 'w') as f:
            f.write('test.txt')

        result = cli_runner.invoke(
            file_put, ['--project-path', 'test', '--thread', 1, '--attribute', 'test.json', 'test.txt']
        )
    assert result.exit_code == 0
    simple_upload_mock.assert_called_once()
    attribute_mock.assert_called_once()


def test_resumable_upload_command_success(mocker, cli_runner):
    mocker.patch('os.path.exists', return_value=True)
    # mock the open function
    mocked_open_data = mocker.mock_open(read_data='test')
    mocker.patch('builtins.open', mocked_open_data)
    mocker.patch('json.load', return_value={'resumable_manifest': 'test.json', 'thread': 1})
    mocker.patch('app.commands.file.resume_upload', return_value=None)

    result = cli_runner.invoke(file_resume, ['--resumable-manifest', 'test.json', '--thread', 1])
    assert result.exit_code == 0


def test_resumable_upload_command_failed_with_file_not_exists(mocker, cli_runner):
    mocker.patch('os.path.exists', return_value=False)

    result = cli_runner.invoke(file_resume, ['--resumable-manifest', 'test.json', '--thread', 1])
    assert result.exit_code == 0
    assert result.output == customized_error_msg(ECustomizedError.INVALID_RESUMABLE) + '\n'
