# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import json
from os import makedirs
from os.path import dirname

import click
import pytest
import questionary

from app.commands.file import file_download
from app.commands.file import file_list
from app.commands.file import file_metadata_download
from app.commands.file import file_move
from app.commands.file import file_put
from app.commands.file import file_resume
from app.models.item import ItemType
from app.services.file_manager.file_metadata.file_metadata_client import FileMetaClient
from app.services.file_manager.file_upload.models import FileObject
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import customized_error_msg
from tests.conftest import decoded_token


def test_file_upload_command_success_with_attribute(mocker, cli_runner):
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
        with open('template.json', 'w') as f:
            json.dump({'template': {'attr1': 'value'}}, f)

        result = cli_runner.invoke(
            file_put,
            [
                '--project-path',
                f'test_project/{ItemType.NAMEFOLDER.get_prefix_by_type()}admin',
                '--thread',
                1,
                '--attribute',
                'template.json',
                'test.txt',
            ],
        )

    assert result.exit_code == 0
    simple_upload_mock.assert_called_once()
    attribute_mock.assert_called_once()


def test_file_upload_failed_with_invalid_tag_file(cli_runner):
    # create invalid tag file with wrong format
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        with open('wrong_tag.json', 'w') as f:
            f.write('wrong_tag.json')

        result = cli_runner.invoke(
            file_put, ['--project-path', 'test', '--thread', 1, '--tag', 'wrong_tag.json', 'wrong_tag.json']
        )
    assert result.exit_code == 0
    assert result.output == customized_error_msg(ECustomizedError.INVALID_TAG_FILE) + '\n'


def test_file_upload_failed_with_invalid_attribute_file(cli_runner):
    # create invalid attribute file with wrong format
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        with open('wrong_attribute.json', 'w') as f:
            f.write('wrong_attribute.json')

        result = cli_runner.invoke(
            file_put,
            ['--project-path', 'test', '--thread', 1, '--attribute', 'wrong_attribute.json', 'wrong_attribute.json'],
        )
    assert result.exit_code == 0
    assert result.output == customized_error_msg(ECustomizedError.INVALID_TEMPLATE) + '\n'


def test_resumable_upload_command_success(mocker, cli_runner):
    mocker.patch('os.path.exists', return_value=True)
    # mock the open function
    mocked_open_data = mocker.mock_open(read_data='test')
    mocker.patch('builtins.open', mocked_open_data)
    mocker.patch('json.load', return_value={'file_objects': {'test_item_id': {'file_name': 'test.json'}}, 'zone': 1})
    mocker.patch('app.commands.file.resume_upload', return_value=None)
    mocker.patch('os.remove', return_value=None)
    result = cli_runner.invoke(file_resume, ['--resumable-manifest', 'test.json', '--thread', 1])
    assert result.exit_code == 0


def test_resumable_upload_command_with_file_attribute_success(mocker, cli_runner):
    mocker.patch('os.path.exists', return_value=True)
    # mock the open function
    mocked_open_data = mocker.mock_open(read_data='test')
    mocker.patch('builtins.open', mocked_open_data)
    mocker.patch(
        'json.load',
        return_value={
            'file_objects': {'test_item_id': {'file_name': 'test.json'}},
            'zone': 1,
            'attributes': {'M1': {'attr1': '1'}},
        },
    )
    mocker.patch('app.commands.file.resume_upload', return_value=None)

    attribute_fun_mock = mocker.patch(
        'app.services.file_manager.file_manifests.SrvFileManifests.attach_manifest', return_value=None
    )

    mocker.patch('os.remove', return_value=None)

    result = cli_runner.invoke(file_resume, ['--resumable-manifest', 'test.json', '--thread', 1])
    assert result.exit_code == 0
    attribute_fun_mock.assert_called_once()


def test_resumable_upload_command_failed_with_file_not_exists(mocker, cli_runner):
    mocker.patch('os.path.exists', return_value=False)

    result = cli_runner.invoke(file_resume, ['--resumable-manifest', 'test.json', '--thread', 1])
    assert result.exit_code == 0
    assert result.output == customized_error_msg(ECustomizedError.INVALID_RESUMABLE) + '\n'


def test_file_list_with_pagination_with_folder_success(requests_mock, mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    mocker.patch(
        'app.services.file_manager.file_list.search_item',
        return_value={
            'result': {
                'type': ItemType.FOLDER.value,
                'id': 'id',
            }
        },
    )
    requests_mock.get(
        'http://bff_cli' + '/v1/testproject/files/query',
        json={
            'code': 200,
            'error_msg': '',
            'result': [
                {'type': ItemType.FILE.value, 'name': 'file1'},
                {'type': ItemType.FILE.value, 'name': 'file2'},
            ],
        },
    )
    mocker.patch.object(questionary, 'select')
    questionary.select.return_value.ask.return_value = 'exit'
    result = cli_runner.invoke(file_list, ['testproject/admin', '-z', 'greenroom'])
    outputs = result.output.split('\n')
    assert outputs[0] == 'file1  file2   '


@pytest.mark.parametrize('parent_folder_type', [ItemType.NAMEFOLDER.value, ItemType.SHAREDFOLDER.value])
def test_file_list_with_pagination_with_root_folder(requests_mock, mocker, cli_runner, parent_folder_type):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    mocker.patch(
        'app.services.file_manager.file_list.search_item',
        return_value={
            'result': {
                'type': parent_folder_type,
                'id': 'id',
            }
        },
    )

    folder = 'folder1'
    folder_with_underline = 'folder_1'
    folder_with_space = 'folder 1'
    requests_mock.get(
        'http://bff_cli' + '/v1/testproject/files/query',
        json={
            'code': 200,
            'error_msg': '',
            'result': [
                {'type': ItemType.FOLDER.value, 'name': folder},
                {'type': ItemType.NAMEFOLDER.value, 'name': folder_with_underline},
                {'type': ItemType.SHAREDFOLDER.value, 'name': folder_with_underline},
                {'type': ItemType.FOLDER.value, 'name': folder_with_space},
                {'type': ItemType.SHAREDFOLDER.value, 'name': folder_with_space},
            ],
        },
    )
    mocker.patch.object(questionary, 'select')
    questionary.select.return_value.ask.return_value = 'exit'
    result = cli_runner.invoke(file_list, ['testproject/admin', '-z', 'greenroom'])
    outputs = result.output.split('\n')
    assert outputs[0] == f'{folder}  {folder_with_underline}  {folder_with_underline}  "{folder_with_space}"  '
    assert outputs[1] == f'"{folder_with_space}"   '


def test_empty_file_list_with_pagination(requests_mock, mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    mocker.patch(
        'app.services.file_manager.file_list.search_item',
        return_value={
            'result': {
                'type': ItemType.FOLDER.value,
                'id': 'id',
            }
        },
    )
    requests_mock.get(
        'http://bff_cli' + '/v1/testproject/files/query',
        json={'code': 200, 'error_msg': '', 'result': []},
    )
    mocker.patch.object(questionary, 'select')
    questionary.select.return_value.ask.return_value = 'exit'
    result = cli_runner.invoke(file_list, ['testproject/admin', '-z', 'greenroom'])
    outputs = result.output.split('\n')
    assert outputs[0] == ' '


@pytest.mark.parametrize('parent_folder_type', [ItemType.NAMEFOLDER.value, ItemType.SHAREDFOLDER.value])
def test_file_download_success(requests_mock, mocker, cli_runner, parent_folder_type):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    search_mock = mocker.patch(
        'app.commands.file.search_item',
        side_effect=[
            {
                'code': 200,
                'result': {
                    'type': parent_folder_type,
                    'name': 'test',
                    'id': 'id',
                },
            },
            {
                'code': 200,
                'result': {
                    'type': ItemType.FILE.value,
                    'id': 'id',
                },
            },
        ],
    )

    download_mock = mocker.patch(
        'app.services.file_manager.file_download.download_client.SrvFileDownload.simple_download_file',
        return_value=None,
    )

    project_code, target_folder = 'testproject', 'test/test.txt'
    result = cli_runner.invoke(file_download, [f'{project_code}/{target_folder}', './'])
    outputs = result.output.split('\n')
    assert outputs[0] == ''

    except_target_folder = 'test/test.txt' if parent_folder_type == 'name_folder' else 'shared/test/test.txt'
    search_mock.assert_called_with(project_code, 'greenroom', except_target_folder)
    download_mock.assert_called_once()


def test_download_file_metadata_file_duplicate_success(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    donwload_metadata_mock = mocker.patch(
        'app.services.file_manager.file_metadata.file_metadata_client.FileMetaClient.download_file_metadata',
        return_value=None,
    )

    metadata_loc = './test'
    file_path = 'project_code/admin/test.py'
    # create a test file
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        file_meta_client = FileMetaClient('zone', file_path, metadata_loc, metadata_loc, metadata_loc)
        # create all file to make duplicationn
        makedirs(dirname(file_meta_client.general_location), exist_ok=True, mode=0o0700)
        with open(file_meta_client.general_location, 'w') as f:
            f.write(file_meta_client.general_location)
        makedirs(dirname(file_meta_client.attribute_location), exist_ok=True, mode=0o0700)
        with open(file_meta_client.attribute_location, 'w') as f:
            f.write(file_meta_client.attribute_location)
        makedirs(dirname(file_meta_client.tag_location), exist_ok=True, mode=0o0700)
        with open(file_meta_client.tag_location, 'w') as f:
            f.write(file_meta_client.tag_location)

        result = cli_runner.invoke(
            file_metadata_download,
            [file_path, '-g', metadata_loc, '-a', metadata_loc, '-t', metadata_loc],
            input='y',
        )

    assert result.exit_code == 0

    outputs = result.output
    excepted_output = (
        customized_error_msg(ECustomizedError.LOCAL_METADATA_FILE_EXISTS)
        + f'\n - general: {file_meta_client.general_location}'
        + f'\n - attribute: {file_meta_client.attribute_location}'
        + f'\n - tag: {file_meta_client.tag_location}\n'
        + 'Do you want to overwrite the existing file? [y/N]: y\n'
        + 'Metadata download complete.\n'
    )
    assert outputs == excepted_output

    donwload_metadata_mock.assert_called_once()


def test_download_file_metadata_file_duplicate_abort(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    donwload_metadata_mock = mocker.patch(
        'app.services.file_manager.file_metadata.file_metadata_client.FileMetaClient.download_file_metadata',
        return_value=None,
    )

    metadata_loc = './test'
    file_path = 'project_code/admin/test.py'
    # create a test file
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        file_meta_client = FileMetaClient('zone', file_path, metadata_loc, metadata_loc, metadata_loc)
        # create all file to make duplicationn
        makedirs(dirname(file_meta_client.general_location), exist_ok=True, mode=0o0700)
        with open(file_meta_client.general_location, 'w') as f:
            f.write(file_meta_client.general_location)
        makedirs(dirname(file_meta_client.attribute_location), exist_ok=True, mode=0o0700)
        with open(file_meta_client.attribute_location, 'w') as f:
            f.write(file_meta_client.attribute_location)
        makedirs(dirname(file_meta_client.tag_location), exist_ok=True, mode=0o0700)
        with open(file_meta_client.tag_location, 'w') as f:
            f.write(file_meta_client.tag_location)

        result = cli_runner.invoke(
            file_metadata_download,
            [file_path, '-g', metadata_loc, '-a', metadata_loc, '-t', metadata_loc],
            input='n',
        )

    assert result.exit_code == 1

    outputs = result.output
    excepted_output = (
        customized_error_msg(ECustomizedError.LOCAL_METADATA_FILE_EXISTS)
        + f'\n - general: {file_meta_client.general_location}'
        + f'\n - attribute: {file_meta_client.attribute_location}'
        + f'\n - tag: {file_meta_client.tag_location}\n'
        + 'Do you want to overwrite the existing file? [y/N]: n\n'
        + 'Metadata download cancelled.\n'
    )
    assert outputs == excepted_output

    assert donwload_metadata_mock.call_count == 0


def test_file_move_success(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    file_move_mock = mocker.patch(
        'app.services.file_manager.file_move.file_move_client.FileMoveClient.move_file',
        return_value=None,
    )

    result = cli_runner.invoke(file_move, ['test_project', 'src_item_path', 'dest_item_path'])
    outputs = result.output.split('\n')
    assert outputs[0] == 'Successfully moved src_item_path to dest_item_path'
    file_move_mock.assert_called_once()
