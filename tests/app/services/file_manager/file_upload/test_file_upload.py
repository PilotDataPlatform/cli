# Copyright (C) 2022-2026 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import os
from unittest.mock import MagicMock

import click

from app.configs.app_config import AppConfig
from app.models.item import ItemType
from app.services.file_manager.file_upload.file_upload import (
    assemble_path,
    compress_folder_to_zip,
    resume_upload,
    simple_upload,
)
from app.services.file_manager.file_upload.models import FileObject, ItemStatus
from app.services.output_manager.error_handler import ECustomizedError, customized_error_msg
from tests.conftest import decoded_token


def test_compress_to_zip(mocker):
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        # create a test folder and file
        test_folder = 'test_folder'
        test_file_content = 'This is a test file.'
        os.makedirs(test_folder, exist_ok=True)
        for i in range(3):
            with open(os.path.join(test_folder, f'test_file_{i}.txt'), 'w') as f:
                f.write(test_file_content)

        # compress the folder
        zip_file_path = compress_folder_to_zip(test_folder)
        assert os.path.exists(zip_file_path)
        assert zip_file_path.endswith('.zip')

        # check the content of the zip file
        import zipfile

        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_content = zip_ref.namelist()
            assert len(zip_content) == 3
            for i in range(3):
                assert f'{test_folder}/test_file_{i}.txt' in zip_content
        # check the content of the files in the zip
        for i in range(3):
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                with zip_ref.open(f'{test_folder}/test_file_{i}.txt') as f:
                    content = f.read().decode('utf-8')
                    assert content == test_file_content


def test_assemble_path_at_name_folder(mocker):
    local_file_path = './test/file.txt'
    target_folder = 'admin'
    project_code = 'test_project'
    zone = 0

    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.search_item',
        return_value={
            'result': {
                'id': 'test',
                'parent_id': 'test_parent',
                'parent_path': '',
                'name': 'admin',
                'zone': 0,
                'type': 'name_folder',
            }
        },
    )

    current_file_path, parent_folder, create_folder_flag, _ = assemble_path(
        local_file_path, target_folder, project_code, ItemType.NAMEFOLDER, zone
    )
    assert current_file_path == f'{ItemType.NAMEFOLDER.get_prefix_by_type()}admin/file.txt'
    assert parent_folder.get('name') == 'admin'
    assert create_folder_flag is False


def test_assemble_path_at_exsting_folder(mocker):
    local_file_path = './test/file.txt'
    target_folder = 'admin/test_folder_exist'
    project_code = 'test_project'
    zone = 0

    node_list = [
        {
            'result': {
                'id': 'test',
                'parent_id': 'test_parent',
                'parent_path': '',
                'name': ItemType.NAMEFOLDER.get_prefix_by_type().strip('/'),
                'zone': 0,
                'type': 'folder',
            }
        },
        {
            'result': {
                'id': 'test',
                'parent_id': 'test_parent',
                'parent_path': ItemType.NAMEFOLDER.get_prefix_by_type(),
                'name': 'admin',
                'zone': 0,
                'type': 'folder',
            }
        },
        {
            'result': {
                'id': 'test',
                'parent_id': 'test_parent',
                'parent_path': ItemType.NAMEFOLDER.get_prefix_by_type() + 'admin',
                'name': 'test_folder_exist',
                'zone': 0,
                'type': 'folder',
            }
        },
    ]

    mocker.patch('app.services.file_manager.file_upload.file_upload.search_item', side_effect=node_list)
    current_file_path, parent_folder, create_folder_flag, _ = assemble_path(
        local_file_path, target_folder, project_code, ItemType.NAMEFOLDER, zone
    )
    assert current_file_path == f'{ItemType.NAMEFOLDER.get_prefix_by_type()}admin/test_folder_exist/file.txt'
    assert parent_folder.get('name') == 'admin'
    assert create_folder_flag is False


def test_assemble_path_at_non_existing_folder(mocker):
    local_file_path = './test/file.txt'
    target_folder = 'admin/test_folder_not_exist'
    project_code = 'test_project'
    zone = 0

    node_list = [
        {
            'result': {
                'id': 'test',
                'parent_id': 'test_parent',
                'parent_path': ItemType.NAMEFOLDER.get_prefix_by_type(),
                'name': 'admin',
                'zone': 0,
                'type': 'folder',
            }
        },
        {'result': {}},
    ]

    mocker.patch('app.services.file_manager.file_upload.file_upload.search_item', side_effect=node_list)
    mocker.patch('app.services.file_manager.file_upload.file_upload.click.confirm', return_value=None)

    current_file_path, parent_folder, create_folder_flag, _ = assemble_path(
        local_file_path, target_folder, project_code, ItemType.NAMEFOLDER, zone
    )
    assert current_file_path == f'{ItemType.NAMEFOLDER.get_prefix_by_type()}admin/test_folder_not_exist'
    assert parent_folder.get('name') == 'admin'
    assert create_folder_flag is True


def test_assemble_path_at_project_folder(mocker):
    local_file_path = './test/file.txt'
    target_folder = ItemType.SHAREDFOLDER.value
    project_code = 'test_project'
    zone = 0

    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.search_item',
        return_value={
            'result': {
                'id': 'test',
                'parent_id': 'test_parent',
                'parent_path': '',
                'name': target_folder,
                'zone': 0,
                'type': target_folder,
            }
        },
    )

    current_file_path, parent_folder, create_folder_flag, target_folder = assemble_path(
        local_file_path, target_folder, project_code, ItemType.SHAREDFOLDER, zone
    )
    assert current_file_path == f'{ItemType.SHAREDFOLDER.get_prefix_by_type()}project_folder/file.txt'
    assert parent_folder.get('name') == 'project_folder'
    assert target_folder == f'{ItemType.SHAREDFOLDER.get_prefix_by_type()}project_folder'
    assert create_folder_flag is False


def test_file_upload_skip_empty_file(mocker, tmp_path, capfd):
    file_name = 'test'
    upload_event = {
        'file': file_name,
        'project_code': 'test_project',
        'zone': 'greenroom',
    }

    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(0, 0))

    simple_upload(upload_event, output_path=str(tmp_path / 'test'))
    out, _ = capfd.readouterr()

    expect = (
        f'Starting upload of: {file_name}\n'
        + 'Skip the file with 0 size: test\n'
        + 'Start checking file duplication\n'
        + 'Checking for file duplication...\n'
    )

    assert expect in out


def test_dont_allow_tagging_when_folder_upload(mocker, capfd):
    file_name = 'test'
    upload_event = {
        'file': file_name,
        'project_code': 'test_project',
        'tags': ['test_tag'],
        'zone': 'greenroom',
    }

    mocker.patch('os.path.isdir', return_value=True)

    try:
        simple_upload(upload_event)
    except SystemExit:
        out, _ = capfd.readouterr()

        expect = (
            f'Starting upload of: {file_name}\n' + customized_error_msg(ECustomizedError.UNSUPPORT_TAG_MANIFEST) + '\n'
        )

        assert out == expect
    else:
        raise AssertionError('SystemExit not raised')


def test_dont_allow_attribute_attaching_when_folder_upload(mocker, capfd):
    file_name = 'test'
    upload_event = {
        'file': file_name,
        'project_code': 'test_project',
        'zone': 'greenroom',
        'attribute': 'test_manifest',
    }

    mocker.patch('os.path.isdir', return_value=True)

    try:
        simple_upload(upload_event)
    except SystemExit:
        out, _ = capfd.readouterr()

        expect = (
            f'Starting upload of: {file_name}\n' + customized_error_msg(ECustomizedError.UNSUPPORT_TAG_MANIFEST) + '\n'
        )

        assert out == expect
    else:
        raise AssertionError('SystemExit not raised')


def test_folder_merge_succuss_with_no_duplication(mocker, mock_upload_client):
    file_name = 'test'
    upload_event = {
        'file': file_name,
        'project_code': 'test_project',
        'zone': 'greenroom',
        'create_folder_flag': False,
    }

    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))

    non_dup_list = [FileObject('object/path', 'local_path', 'resumable_id', 'job_id', 'item_id')]
    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.UploadClient.check_upload_duplication',
        return_value=(non_dup_list, [], []),
    )

    item_ids = simple_upload(upload_event)
    assert len(item_ids) == 1
    assert item_ids[0] == non_dup_list[0].item_id


def test_folder_merge_succuss_with_duplication(mocker, mock_upload_client):
    file_name = 'test'
    upload_event = {
        'file': file_name,
        'project_code': 'test_project',
        'zone': 'greenroom',
        'create_folder_flag': False,
    }

    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    click_yes_mock = mocker.patch('app.services.file_manager.file_upload.file_upload.click.confirm', return_value=None)

    non_dup_list = [FileObject('object/path', 'local_path', 'resumable_id', 'job_id', 'item_id')]
    dup_list = ['object/dup']
    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.UploadClient.check_upload_duplication',
        return_value=(non_dup_list, dup_list, []),
    )

    item_ids = simple_upload(upload_event)
    assert len(item_ids) == 1
    assert item_ids[0] == non_dup_list[0].item_id
    assert click_yes_mock.call_count == 1


def test_folder_merge_skip_with_all_duplication(mocker, mock_upload_client, capfd):
    file_name = 'test'
    upload_event = {
        'file': file_name,
        'project_code': 'test_project',
        'zone': 'greenroom',
        'create_folder_flag': False,
    }

    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    click_yes_mock = mocker.patch('app.services.file_manager.file_upload.file_upload.click.confirm', return_value=None)

    dup_list = ['object/dup']
    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.UploadClient.check_upload_duplication',
        return_value=([], dup_list, []),
    )

    try:
        simple_upload(upload_event)

    except SystemExit:
        assert click_yes_mock.call_count == 0

        out, _ = capfd.readouterr()
        expect = (
            f'Starting upload of: {file_name}\n'
            + 'Start checking file duplication\n'
            + 'Checking for file duplication...\n'
            + '\nAll files already exist in the upload destination.\n\n'
            + customized_error_msg(ECustomizedError.UPLOAD_CANCEL)
            + '\n'
        )
        assert expect in out
    else:
        raise AssertionError('SystemExit not raised')


def test_upload_folder_as_zip(mocker, mock_upload_client):
    test_folder = 'test'
    upload_event = {
        'file': test_folder,
        'project_code': 'test_project',
        'zone': 'greenroom',
        'create_folder_flag': False,
        'compress_zip': True,
    }

    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    compress_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.compress_folder_to_zip', return_value='test.zip'
    )

    non_dup_list = [FileObject('object/path', 'local_path', 'resumable_id', 'job_id', 'item_id')]
    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.UploadClient.check_upload_duplication',
        return_value=(non_dup_list, [], []),
    )
    item_ids = simple_upload(upload_event)
    assert len(item_ids) == 1
    assert item_ids[0] == non_dup_list[0].item_id
    assert compress_mock.call_count == 1


def test_resume_upload(mocker):
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    test_obj = FileObject('object/path', 'local_path', 'resumable_id', 'job_id', 'item_id')
    test_obj.total_size = 1

    manifest_json = {
        'project_code': 'project_code',
        'operator': 'operator',
        'zone': AppConfig.Env.green_zone,
        'parent_folder_id': 'parent_folder_id',
        'current_folder_node': 'current_folder_node',
        'tags': 'tags',
        'registered_items': {test_obj.item_id: test_obj.to_dict()},
        'unregistered_items': {},
        'total_size': 1,
        'resumable_manifest_file': 'resumable_manifest_file',
    }

    get_return = test_obj.to_dict()
    get_return.update({'status': ItemStatus.REGISTERED})
    get_return.update({'id': get_return.get('item_id')})
    get_return.update({'size': 1})
    get_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.get_file_info_by_geid', return_value=[{'result': get_return}]
    )
    resume_upload_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.UploadClient.resume_upload', return_value=[]
    )
    mocker.patch(
        'os.path.getsize',
        return_value=1,
    )
    output_manifest_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.UploadClient.output_manifest', return_value={}
    )

    resume_upload(manifest_json, 1)

    get_mock.assert_called_once()
    resume_upload_mock.assert_called_once()
    output_manifest_mock.assert_called_once()


def test_resume_upload_failed_when_REGISTERED_doesnt_exist(mocker, capfd):
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    test_obj = FileObject('object/path', 'local_path', 'resumable_id', 'job_id', 'item_id')

    manifest_json = {
        'project_code': 'project_code',
        'operator': 'operator',
        'zone': AppConfig.Env.green_zone,
        'parent_folder_id': 'parent_folder_id',
        'current_folder_node': 'current_folder_node',
        'tags': 'tags',
        'registered_items': {test_obj.item_id: test_obj.to_dict()},
        'unregistered_items': {},
        'resumable_manifest_file': 'resumable_manifest_file',
    }

    get_return = test_obj.to_dict()
    get_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.get_file_info_by_geid',
        return_value=[{'result': {}, 'geid': get_return.get('item_id')}],
    )
    resume_upload_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.UploadClient.resume_upload', return_value=[]
    )
    resumable_manifest_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.UploadClient.output_manifest', return_value={}
    )

    try:
        resume_upload(manifest_json, 1)
    except SystemExit:
        out, _ = capfd.readouterr()
        expect = customized_error_msg(ECustomizedError.INVALID_RESUMABLE_UPLOAD) % ('object/path') + '\n'
        assert expect in out

    get_mock.assert_called_once()
    assert resume_upload_mock.call_count == 0
    assert resumable_manifest_mock.call_count == 0


def test_resume_upload_integrity_check_failed(mocker, capfd):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    test_obj = FileObject('object/path', 'local_path', 'resumable_id', 'job_id', 'item_id')
    test_obj.total_size = 2  # wrong size

    manifest_json = {
        'project_code': 'project_code',
        'operator': 'operator',
        'zone': AppConfig.Env.green_zone,
        'parent_folder_id': 'parent_folder_id',
        'current_folder_node': 'current_folder_node',
        'tags': 'tags',
        'registered_items': {test_obj.item_id: test_obj.to_dict()},
        'unregistered_items': {},
        'total_size': 1,
    }

    get_return = test_obj.to_dict()
    get_return.update({'status': ItemStatus.REGISTERED})
    get_return.update({'id': get_return.get('item_id')})
    get_return.update({'size': 1})
    get_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.get_file_info_by_geid', return_value=[{'result': get_return}]
    )
    resume_upload_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.UploadClient.resume_upload', return_value=[]
    )
    mocker.patch(
        'os.path.getsize',
        return_value=2,
    )
    resumable_manifest_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.UploadClient.output_manifest', return_value={}
    )

    resume_upload(manifest_json, 1)
    out, _ = capfd.readouterr()
    expect = customized_error_msg(ECustomizedError.INVALID_RESUMABLE_FILE_SIZE) % ('object/path', 1, 2)
    assert expect in out

    get_mock.assert_called_once()
    resume_upload_mock.assert_called_once()
    resumable_manifest_mock.assert_called_once()


def test_resume_upload_manifest_updates_correctly_after_each_batch(mocker):
    """
    Test that the manifest file is updated correctly after each batch,
    ensuring the remaining unregistered_items slice is accurate.
    """
    # Mock dependencies
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))

    # Create test file objects
    test_files = []
    for i in range(7):  # 7 files, with batch size of 3, should be 3 batches: [3, 3, 1]
        test_obj = FileObject(f'object/path_{i}', f'local_path_{i}', f'resumable_id_{i}', f'job_id_{i}', f'item_id_{i}')
        test_obj.total_size = 1
        test_files.append(test_obj)

    manifest_json = {
        'project_code': 'project_code',
        'operator': 'operator',
        'zone': AppConfig.Env.green_zone,
        'parent_folder_id': 'parent_folder_id',
        'current_folder_node': 'current_folder_node',
        'tags': 'tags',
        'registered_items': {},
        'unregistered_items': {f'object/path_{i}': test_files[i].to_dict() for i in range(7)},
        'total_size': 7,
        'resumable_manifest_file': 'test_manifest.json',
    }

    # Mock the upload client and its methods
    mock_upload_client = MagicMock()
    mock_upload_client.pre_upload.return_value = []  # Return empty list for simplicity

    # Track calls to output_manifest to verify correct remaining items
    manifest_calls = []

    def track_manifest_calls(finished_items, remaining_items, manifest_file):
        manifest_calls.append(
            {
                'finished_count': len(finished_items),
                'remaining_count': len(remaining_items),
                'remaining_items': [
                    item.object_path if hasattr(item, 'object_path') else str(item) for item in remaining_items
                ],
            }
        )

    mock_upload_client.output_manifest.side_effect = track_manifest_calls

    # Mock the UploadClient constructor
    mocker.patch('app.services.file_manager.file_upload.file_upload.UploadClient', return_value=mock_upload_client)

    # Mock other dependencies
    mocker.patch('app.services.file_manager.file_upload.file_upload.resume_get_unfinished_items', return_value=[])
    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.item_duplication_check', return_value=(test_files, [])
    )  # Return all files as unregistered
    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.batch_generator',
        side_effect=lambda items, batch_size: [items[i : i + batch_size] for i in range(0, len(items), batch_size)],
    )

    # Set batch size to 3 for testing
    mocker.patch.object(AppConfig.Env, 'upload_batch_size', 3)

    # Mock threading components
    mocker.patch('app.services.file_manager.file_upload.file_upload.ThreadPool')
    mocker.patch('app.services.output_manager.message_handler.SrvOutPutHandler')

    # Execute the function
    resume_upload(manifest_json, 1)

    # Verify output_manifest was called correctly for each batch
    # Should be called 4 times: 1 initial + 3 batch calls
    expected_calls = 4
    assert len(manifest_calls) == expected_calls, f"Expected {expected_calls} manifest calls, got {len(manifest_calls)}"

    # Verify the remaining items count decreases correctly after each batch
    batch_calls = manifest_calls[1:]  # Skip the initial call, focus on batch processing

    # First batch: processed 3, remaining 4
    assert (
        batch_calls[0]['remaining_count'] == 4
    ), f"After batch 1, expected 4 remaining, got {batch_calls[0]['remaining_count']}"

    # Second batch: processed 6, remaining 1
    assert (
        batch_calls[1]['remaining_count'] == 1
    ), f"After batch 2, expected 1 remaining, got {batch_calls[1]['remaining_count']}"

    # Third batch: processed 7, remaining 0
    assert (
        batch_calls[2]['remaining_count'] == 0
    ), f"After batch 3, expected 0 remaining, got {batch_calls[2]['remaining_count']}"

    # Verify the actual remaining items are correct (not just the count)
    # After first batch, should have items 3,4,5,6 remaining
    expected_remaining_after_batch1 = ['object/path_3', 'object/path_4', 'object/path_5', 'object/path_6']
    assert batch_calls[0]['remaining_items'] == expected_remaining_after_batch1

    # After second batch, should have item 6 remaining
    expected_remaining_after_batch2 = ['object/path_6']
    assert batch_calls[1]['remaining_items'] == expected_remaining_after_batch2

    # After third batch, should have no items remaining
    assert batch_calls[2]['remaining_items'] == []


def test_resume_upload_manifest_handles_uneven_batches(mocker):
    """
    Test that manifest updates work correctly with uneven batch sizes
    (e.g., when the last batch has fewer items than batch_size)
    """
    # Mock dependencies
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))

    # Create 5 test files with batch size of 3 -> batches: [3, 2]
    test_files = []
    for i in range(5):
        test_obj = FileObject(f'object/path_{i}', f'local_path_{i}', f'resumable_id_{i}', f'job_id_{i}', f'item_id_{i}')
        test_obj.total_size = 1
        test_files.append(test_obj)

    manifest_json = {
        'project_code': 'project_code',
        'operator': 'operator',
        'zone': AppConfig.Env.green_zone,
        'parent_folder_id': 'parent_folder_id',
        'current_folder_node': 'current_folder_node',
        'tags': 'tags',
        'registered_items': {},
        'unregistered_items': {f'object/path_{i}': test_files[i].to_dict() for i in range(5)},
        'total_size': 5,
        'resumable_manifest_file': 'test_manifest.json',
    }

    # Mock the upload client
    mock_upload_client = MagicMock()
    mock_upload_client.pre_upload.return_value = []

    # Track manifest calls
    manifest_calls = []

    def track_manifest_calls(finished_items, remaining_items, manifest_file):
        manifest_calls.append(
            {
                'remaining_count': len(remaining_items),
            }
        )

    mock_upload_client.output_manifest.side_effect = track_manifest_calls

    # Mock dependencies
    mocker.patch('app.services.file_manager.file_upload.file_upload.UploadClient', return_value=mock_upload_client)
    mocker.patch('app.services.file_manager.file_upload.file_upload.resume_get_unfinished_items', return_value=[])
    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.item_duplication_check', return_value=(test_files, [])
    )
    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.batch_generator',
        side_effect=lambda items, batch_size: [items[i : i + batch_size] for i in range(0, len(items), batch_size)],
    )

    # Set batch size to 3
    mocker.patch.object(AppConfig.Env, 'upload_batch_size', 3)

    # Mock threading components
    mocker.patch('app.services.file_manager.file_upload.file_upload.ThreadPool')
    mocker.patch('app.services.output_manager.message_handler.SrvOutPutHandler')

    # Execute the function
    resume_upload(manifest_json, 1)

    # Should have 3 calls: 1 initial + 2 batch calls
    batch_calls = manifest_calls[1:]  # Skip initial call

    # After first batch (3 items processed): remaining = 2
    assert batch_calls[0]['remaining_count'] == 2

    # After second batch (5 items processed): remaining = 0
    assert batch_calls[1]['remaining_count'] == 0
