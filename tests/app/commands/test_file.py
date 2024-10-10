# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import json
from os import makedirs
from os.path import dirname
from unittest.mock import Mock

import click
import pytest
import questionary

from app.commands.file import file_download
from app.commands.file import file_list
from app.commands.file import file_metadata_download
from app.commands.file import file_move
from app.commands.file import file_put
from app.commands.file import file_resume
from app.commands.file import file_trash
from app.models.item import ItemType
from app.services.file_manager.file_metadata.file_metadata_client import FileMetaClient
from app.services.file_manager.file_upload.models import FileObject
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import customized_error_msg
from tests.conftest import decoded_token


@pytest.mark.parametrize('ending_slash', ['', '/'])
def test_file_upload_command_success_with_attribute(mocker, cli_runner, ending_slash):
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
                f'test_project/{ItemType.NAMEFOLDER.get_prefix_by_type()}admin' + ending_slash,
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

        result = cli_runner.invoke(file_put, ['test', '--thread', 1, '--tag', 'wrong_tag.json', 'wrong_tag.json'])
    assert result.exit_code == 1
    assert result.output == customized_error_msg(ECustomizedError.INVALID_TAG_FILE) + '\n'


def test_file_upload_failed_with_invalid_attribute_file(cli_runner):
    # create invalid attribute file with wrong format
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        with open('wrong_attribute.json', 'w') as f:
            f.write('wrong_attribute.json')

        result = cli_runner.invoke(
            file_put,
            ['test', '--thread', 1, '--attribute', 'wrong_attribute.json', 'wrong_attribute.json'],
        )
    assert result.exit_code == 1
    assert result.output == customized_error_msg(ECustomizedError.INVALID_TEMPLATE) + '\n'


def test_resumable_upload_command_success(mocker, cli_runner):
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        mocker.patch('os.path.exists', return_value=True)
        with open('test.json', 'w') as f:
            json.dump({'file_objects': {'test_item_id': {'file_name': 'test.json'}}, 'zone': 1}, f)

        mocker.patch('app.commands.file.resume_upload', return_value=None)
        mocker.patch('os.remove', return_value=None)
        result = cli_runner.invoke(file_resume, ['--resumable-manifest', 'test.json', '--thread', 1])

    assert result.exit_code == 0


def test_resumable_upload_command_with_file_attribute_success(mocker, cli_runner):
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        mocker.patch('os.path.exists', return_value=True)
        with open('test.json', 'w') as f:
            json.dump(
                {
                    'file_objects': {'test_item_id': {'file_name': 'test.json'}},
                    'zone': 1,
                    'attributes': {'M1': {'attr1': '1'}},
                },
                f,
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
    assert result.exit_code == 1
    assert result.output == customized_error_msg(ECustomizedError.INVALID_RESUMABLE) + '\n'


@pytest.mark.parametrize(
    'page, options',
    [(0, ['next page', 'exit']), (1, ['next page', 'previous page', 'exit']), (2, ['previous page', 'exit'])],
)
def test_file_list_with_pagination_with_folder_success(httpx_mock, mocker, cli_runner, page, options):
    page_size, total = 9, 20

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    mock_page = {
        0: [0, 1],
        1: [1, 2],
        2: [2, 1],
    }
    for i in mock_page.get(page):
        httpx_mock.add_response(
            method='GET',
            url='http://bff_cli/v1/testproject/files/query?project_code=testproject&folder=users%2F'
            f'admin&source_type=project&zone=greenroom&page={i}&page_size={page_size}&status=ACTIVE',
            json={
                'code': 200,
                'error_msg': '',
                'total': total,
                # generate 20 items
                'result': [{'type': ItemType.FILE.value, 'name': f'f{i}'} for i in range(page_size)],
            },
        )
    clear_mock = mocker.patch('click.clear', return_value=None)

    question_mock = mocker.patch.object(questionary, 'select', return_value=questionary.select)
    questionary.select.return_value.ask = Mock()
    questionary.select.return_value.ask.side_effect = options

    result = cli_runner.invoke(
        file_list, ['testproject/users/admin', '-z', 'greenroom', '--page', page, '--page-size', page_size]
    )
    assert result.exit_code == 0
    assert question_mock.call_count == len(options)
    assert clear_mock.call_count == len(options) - 1

    outputs = result.output.split('\n')
    assert outputs[0] == ''.join([f'f{i}  ' for i in range(page_size)]) + ' '
    assert outputs[1] == ''.join([f'f{i}  ' for i in range(page_size)]) + ' '


def test_file_list_in_trashbin(httpx_mock, mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    httpx_mock.add_response(
        method='GET',
        url='http://bff_cli/v1/testproject/files/query?project_code=testproject&folder=&'
        'source_type=project&zone=&page=0&page_size=10&status=TRASHED',
        json={
            'code': 200,
            'error_msg': '',
            'total': 1,
            'result': [
                {'type': ItemType.FILE.value, 'name': 'test.txt', 'zone': 0, 'status': 'TRASHED'},
                {'type': ItemType.FILE.value, 'name': 'test1.txt', 'zone': 1, 'status': 'TRASHED'},
            ],
        },
    )
    # mocker.patch.object(questionary, 'select')
    # questionary.select.return_value.ask.return_value = 'exit'
    result = cli_runner.invoke(file_list, ['testproject/trash'])
    assert result.exit_code == 0
    outputs = result.output.split('\n')
    assert outputs[0] == 'test.txt(greenroom)  test1.txt(core)   '


def test_file_list_with_pagination_with_root_folder(httpx_mock, mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    folder = 'folder1'
    folder_with_underline = 'folder_1'
    folder_with_space = 'folder 1'
    root_folder = 'root_folder'
    httpx_mock.add_response(
        method='GET',
        url='http://bff_cli/v1/testproject/files/query?project_code=testproject&folder=users%2F'
        'admin&source_type=project&zone=greenroom&page=0&page_size=10&status=ACTIVE',
        json={
            'code': 200,
            'error_msg': '',
            'total': 6,
            'result': [
                {'type': ItemType.FOLDER.value, 'name': folder},
                {'type': ItemType.NAMEFOLDER.value, 'name': folder_with_underline},
                {'type': ItemType.SHAREDFOLDER.value, 'name': folder_with_underline},
                {'type': ItemType.FOLDER.value, 'name': folder_with_space},
                {'type': ItemType.SHAREDFOLDER.value, 'name': folder_with_space},
                {'type': ItemType.ROOTFOLDER.value, 'name': root_folder},
            ],
        },
    )
    select_mock = mocker.patch.object(questionary, 'select')
    questionary.select.return_value.ask.return_value = 'exit'
    result = cli_runner.invoke(file_list, ['testproject/users/admin', '-z', 'greenroom'])
    assert result.exit_code == 0
    assert select_mock.call_count == 0

    outputs = result.output.split('\n')
    assert outputs[0] == f'{folder}  {folder_with_underline}  {folder_with_underline}  "{folder_with_space}"  '
    assert outputs[1] == f'"{folder_with_space}"  {root_folder}   '


def test_empty_file_list_with_pagination(httpx_mock, mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    httpx_mock.add_response(
        method='GET',
        url='http://bff_cli/v1/testproject/files/query?project_code=testproject&'
        'folder=&source_type=project&zone=greenroom&page=0&page_size=10&status=ACTIVE',
        json={'code': 200, 'error_msg': '', 'result': [], 'total': 0},
    )
    mocker.patch.object(questionary, 'select')
    questionary.select.return_value.ask.return_value = 'exit'
    result = cli_runner.invoke(file_list, ['testproject/admin', '-z', 'greenroom'])
    assert result.exit_code == 0
    outputs = result.output.split('\n')
    assert outputs[0] == ' '


@pytest.mark.parametrize('parent_folder_type', [ItemType.NAMEFOLDER, ItemType.SHAREDFOLDER])
def test_file_download_success(mocker, cli_runner, parent_folder_type):
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
                    'type': parent_folder_type.value,
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

    project_code, target_folder = 'testproject', parent_folder_type.get_prefix_by_type() + 'test/test.txt'
    result = cli_runner.invoke(file_download, [f'{project_code}/{target_folder}', './'])
    outputs = result.output.split('\n')
    assert outputs[0] == ''

    search_mock.assert_called_with(project_code, 'greenroom', target_folder)
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

    project_code = 'test_project'
    src_path = f'{project_code}/src_item_path/test/file.txt'
    dest_path = f'{project_code}/dest_item_path/test/file1.txt'
    result = cli_runner.invoke(file_move, [src_path, dest_path])

    outputs = result.output.split('\n')
    assert outputs[0] == f'Successfully moved {src_path} to {dest_path}'
    file_move_mock.assert_called_once()


@pytest.mark.parametrize('src_path', ['src_item_path', 'src_item_path/test'])
def test_file_move_failed_with_invalid_src(mocker, cli_runner, src_path):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    project_code = 'test_project'
    src_path = f'{project_code}/{src_path}'
    dest_path = f'{project_code}/dest_item_path/test/file1.txt'
    result = cli_runner.invoke(file_move, [src_path, dest_path])
    assert result.exit_code == 1

    outputs = result.output.split('\n')
    assert outputs[0] == f'Failed to move {src_path} to {dest_path}: Cannot move root/name/shared folders'


@pytest.mark.parametrize('dest_path', ['dest_item_path'])
def test_file_move_failed_with_invalid_dest(mocker, cli_runner, dest_path):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    project_code = 'test_project'
    src_path = f'{project_code}/src_item_path/test/file.txt'
    dest_path = f'{project_code}/{dest_path}'
    result = cli_runner.invoke(file_move, [src_path, dest_path])
    assert result.exit_code == 1

    outputs = result.output.split('\n')
    assert outputs[0] == f'Failed to move {src_path} to {dest_path}: Cannot move root/name/shared folders'


def test_file_move_failed_with_mismatched_project_code(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    project_code = 'test_project'
    src_path = f'{project_code}/src_item_path/test/file.txt'
    dest_path = 'wrong_project/dest_item_path/test/file1.txt'
    result = cli_runner.invoke(file_move, [src_path, dest_path])
    assert result.exit_code == 1

    outputs = result.output.split('\n')
    assert outputs[0] == f'Failed to move {src_path} to {dest_path}: Cannot move files between different projects'


def test_file_trash_success(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    search_mock = mocker.patch(
        'app.services.file_manager.file_trash.utils.search_item',
        side_effect=[
            {
                'code': 200,
                'result': {
                    'type': ItemType.FILE.value,
                    'parent_path': 'users/admin',
                    'name': 'test.txt',
                    'id': 'id',
                },
            },
            {
                'code': 200,
                'result': {
                    'type': ItemType.FOLDER.value,
                    'parent_path': 'users',
                    'name': 'admin',
                    'id': 'id',
                },
            },
        ],
    )
    file_trash_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.move_to_trash',
        return_value=None,
    )
    status_check_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.check_status',
        return_value=[],
    )

    project_code = 'testproject'
    file_path = f'{project_code}/users/admin/test.txt'
    result = cli_runner.invoke(file_trash, [file_path, '-z', 'greenroom'])

    outputs = result.output.split('\n')
    assert outputs[0] == 'Items: [\'testproject/users/admin/test.txt\'] have been trashed successfully.'

    assert search_mock.call_count == 2
    file_trash_mock.assert_called_once()
    status_check_mock.assert_called_once()


def test_file_trash_failed_with_invalid_path(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    project_code = 'testproject'
    file_path = f'{project_code}/admin/test.txt'
    result = cli_runner.invoke(file_trash, [file_path, '-z', 'greenroom'])
    assert result.exit_code == 1

    outputs = result.output.split('\n')
    assert outputs[0] == 'Selected path: testproject/admin/test.txt is invalid.'


def test_file_trash_failed_with_item_not_exist(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    search_mock = mocker.patch(
        'app.services.file_manager.file_trash.utils.search_item',
        side_effect=[
            {
                'code': 404,
                'result': {},
            },
        ],
    )

    project_code = 'testproject'
    file_path = f'{project_code}/users/admin/test.txt'
    result = cli_runner.invoke(file_trash, [file_path, '-z', 'greenroom'])
    assert result.exit_code == 1

    outputs = result.output.split('\n')
    assert outputs[0] == 'Selected path: testproject/users/admin/test.txt does not exist.'
    assert search_mock.call_count == 1


def test_file_trash_with_trash_failed(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    search_mock = mocker.patch(
        'app.services.file_manager.file_trash.utils.search_item',
        side_effect=[
            {
                'code': 200,
                'result': {
                    'type': ItemType.FILE.value,
                    'parent_path': 'users/admin',
                    'name': 'test.txt',
                    'id': 'id',
                },
            },
            {
                'code': 200,
                'result': {
                    'type': ItemType.FOLDER.value,
                    'parent_path': 'users',
                    'name': 'admin',
                    'id': 'id',
                },
            },
        ],
    )
    file_trash_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.move_to_trash',
        return_value=None,
    )
    status_check_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.check_status',
        return_value=['users/admin/test.txt'],
    )

    project_code = 'testproject'
    file_path = f'{project_code}/users/admin/test.txt'
    result = cli_runner.invoke(file_trash, [file_path, '-z', 'greenroom'])
    assert result.exit_code == 1

    outputs = result.output.split('\n')
    assert outputs[0] == 'Failed to trash items: [\'users/admin/test.txt\'].'

    assert search_mock.call_count == 2
    file_trash_mock.assert_called_once()
    status_check_mock.assert_called_once()


def test_file_permanent_delete_success(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    search_mock = mocker.patch(
        'app.services.file_manager.file_trash.utils.search_item',
        side_effect=[
            {
                'code': 200,
                'result': {
                    'type': ItemType.FILE.value,
                    'parent_path': 'users/admin',
                    'name': 'test.txt',
                    'id': 'id',
                },
            },
            {
                'code': 200,
                'result': {
                    'type': ItemType.FOLDER.value,
                    'parent_path': 'users',
                    'name': 'admin',
                    'id': 'id',
                },
            },
        ],
    )
    file_trash_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.move_to_trash',
        return_value=None,
    )
    status_check_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.check_status',
        return_value=[],
    )

    file_delete_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.permanently_delete',
        return_value=None,
    )

    project_code = 'testproject'
    file_path = f'{project_code}/users/admin/test.txt'
    result = cli_runner.invoke(file_trash, [file_path, '-z', 'greenroom', '--permanent'])

    outputs = result.output.split('\n')
    assert outputs[0] == 'Items: [\'testproject/users/admin/test.txt\'] have been permanently deleted successfully.'

    assert search_mock.call_count == 2
    file_trash_mock.assert_called_once()
    file_delete_mock.assert_called_once()
    assert status_check_mock.call_count == 2


def test_file_permanent_delete_from_trash_success(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    search_mock = mocker.patch(
        'app.services.file_manager.file_trash.utils.search_item',
        side_effect=[
            {
                'code': 200,
                'result': {
                    'type': ItemType.FILE.value,
                    'parent_path': '',
                    'name': 'test.txt',
                    'id': 'id',
                },
            },
            {
                'code': 404,
                'result': {},
            },
        ],
    )
    file_trash_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.move_to_trash',
        return_value=None,
    )
    status_check_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.check_status',
        return_value=[],
    )

    file_delete_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.permanently_delete',
        return_value=None,
    )

    project_code = 'testproject'
    file_path = f'{project_code}/trash/test.txt'
    result = cli_runner.invoke(file_trash, [file_path, '-z', 'greenroom', '--permanent'])

    outputs = result.output.split('\n')
    assert outputs[0] == 'Items: [\'testproject/trash/test.txt\'] have been permanently deleted successfully.'

    assert search_mock.call_count == 2
    assert file_trash_mock.call_count == 0
    file_delete_mock.assert_called_once()
    assert status_check_mock.call_count == 1


def test_file_delete_from_trash_fail(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    project_code = 'testproject'
    file_path = f'{project_code}/trash/test.txt'
    result = cli_runner.invoke(file_trash, [file_path, '-z', 'greenroom'])
    assert result.exit_code == 1

    outputs = result.output.split('\n')
    assert (
        outputs[0] == 'Selected path: testproject/trash/test.txt is already in the trash. '
        'Please use permanent delete to remove it.'
    )


def test_file_permanent_delete_with_delete_failed(mocker, cli_runner):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    search_mock = mocker.patch(
        'app.services.file_manager.file_trash.utils.search_item',
        side_effect=[
            {
                'code': 200,
                'result': {
                    'type': ItemType.FILE.value,
                    'parent_path': 'users/admin',
                    'name': 'test.txt',
                    'id': 'id',
                },
            },
            {
                'code': 200,
                'result': {
                    'type': ItemType.FOLDER.value,
                    'parent_path': 'users',
                    'name': 'admin',
                    'id': 'id',
                },
            },
        ],
    )
    file_trash_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.move_to_trash',
        return_value=None,
    )
    status_check_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.check_status',
    )
    status_check_mock.side_effect = [[], ['users/admin/test.txt']]
    file_delete_mock = mocker.patch(
        'app.services.file_manager.file_trash.file_trash_client.FileTrashClient.permanently_delete',
        return_value=None,
    )

    project_code = 'testproject'
    file_path = f'{project_code}/users/admin/test.txt'
    result = cli_runner.invoke(file_trash, [file_path, '-z', 'greenroom', '--permanent'])

    outputs = result.output.split('\n')
    assert outputs[0] == 'Failed to delete items: [\'users/admin/test.txt\'].'

    assert search_mock.call_count == 2
    file_trash_mock.assert_called_once()
    file_delete_mock.assert_called_once()
    assert status_check_mock.call_count == 2
