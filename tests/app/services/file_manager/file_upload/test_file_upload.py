# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from app.configs.app_config import AppConfig
from app.models.item import ItemType
from app.services.file_manager.file_upload.file_upload import assemble_path
from app.services.file_manager.file_upload.file_upload import resume_upload
from app.services.file_manager.file_upload.file_upload import simple_upload
from app.services.file_manager.file_upload.models import FileObject
from app.services.file_manager.file_upload.models import ItemStatus
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import customized_error_msg


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
    assert parent_folder.get('name') == 'test_folder_exist'
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
    target_folder = 'project_folder'
    project_code = 'test_project'
    zone = 0

    mocker.patch(
        'app.services.file_manager.file_upload.file_upload.search_item',
        return_value={
            'result': {
                'id': 'test',
                'parent_id': 'test_parent',
                'parent_path': '',
                'name': 'project_folder',
                'zone': 0,
                'type': 'project_folder',
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

    try:
        simple_upload(upload_event, output_path=str(tmp_path / 'test'))
    except SystemExit:
        out, _ = capfd.readouterr()

        expect = (
            f'Starting upload of: {file_name}\n'
            + 'Skip the file with 0 size: test\n'
            + 'Checking for file duplication...\n'
            + '\nAll files already exist in the upload destination.\n\n'
            + customized_error_msg(ECustomizedError.UPLOAD_CANCEL)
            + '\n'
        )

        assert out == expect
    else:
        AssertionError('SystemExit not raised')


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
        AssertionError('SystemExit not raised')


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
        AssertionError('SystemExit not raised')


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
        return_value=(non_dup_list, []),
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
        return_value=(non_dup_list, dup_list),
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
        return_value=([], dup_list),
    )

    try:
        simple_upload(upload_event)

    except SystemExit:
        assert click_yes_mock.call_count == 0

        out, _ = capfd.readouterr()
        expect = (
            f'Starting upload of: {file_name}\n'
            + 'Checking for file duplication...\n'
            + '\nAll files already exist in the upload destination.\n\n'
            + customized_error_msg(ECustomizedError.UPLOAD_CANCEL)
            + '\n'
        )
        assert expect in out
    else:
        AssertionError('SystemExit not raised')


def test_resume_upload(mocker):
    mocker.patch('app.services.file_manager.file_upload.models.FileObject.generate_meta', return_value=(1, 1))
    test_obj = FileObject('object/path', 'local_path', 'resumable_id', 'job_id', 'item_id')

    manifest_json = {
        'project_code': 'project_code',
        'operator': 'operator',
        'zone': AppConfig.Env.green_zone,
        'parent_folder_id': 'parent_folder_id',
        'current_folder_node': 'current_folder_node',
        'tags': 'tags',
        'file_objects': {test_obj.item_id: test_obj.to_dict()},
    }

    get_return = test_obj.to_dict()
    get_return.update({'status': ItemStatus.REGISTERED})
    get_return.update({'id': get_return.get('item_id')})
    get_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.get_file_info_by_geid', return_value=[{'result': get_return}]
    )
    resume_upload_mock = mocker.patch(
        'app.services.file_manager.file_upload.file_upload.UploadClient.resume_upload', return_value=[]
    )

    resume_upload(manifest_json, 1)

    get_mock.assert_called_once()
    resume_upload_mock.assert_called_once()
