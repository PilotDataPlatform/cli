# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

from app.commands.file import file_resume
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import customized_error_msg


def test_resumable_upload_command_success(mocker, cli_runner):
    mocker.patch('os.path.exists', return_value=True)
    # mock the open function
    mocked_open_data = mocker.mock_open(read_data='test')
    mocker.patch('builtins.open', mocked_open_data)
    mocker.patch('json.load', return_value={'resumable_file': 'test.json', 'thread': 1})
    mocker.patch('app.commands.file.resume_upload', return_value=None)

    result = cli_runner.invoke(file_resume, ['--resumable-file', 'test.json', '--thread', 1])
    assert result.exit_code == 0


def test_resumable_upload_command_failed_with_file_not_exists(mocker, cli_runner):
    mocker.patch('os.path.exists', return_value=False)

    result = cli_runner.invoke(file_resume, ['--resumable-file', 'test.json', '--thread', 1])
    assert result.exit_code == 0
    assert result.output == customized_error_msg(ECustomizedError.INVALID_RESUMABLE) + '\n'
