# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pytest

from app.configs.app_config import AppConfig
from app.models.item import ItemType
from app.services.file_manager.file_metadata.file_metadata_client import FileMetaClient
from tests.conftest import decoded_token


@pytest.mark.parametrize(
    'root_folder',
    [ItemType.NAMEFOLDER, ItemType.SHAREDFOLDER],
)
def test_file_metadata_client_get_detail_success(mocker, httpx_mock, root_folder: ItemType):
    file_name = 'test_file.txt'
    project_code = 'project_code'
    item_info = {
        'id': 'test',
        'parent_id': 'test_parent',
        'parent_path': root_folder.get_prefix_by_type(),
        'name': file_name,
        'zone': 0,
        'status': 'ACTIVE',
        'container_code': project_code,
        'container_type': 'project',
    }
    tags = ['test']
    attri_template_uid = 'template_uid'
    attri_template_name = 'template_name'
    attributes = {attri_template_uid: {'attr_1': 'value'}}

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    mocker.patch(
        'app.services.file_manager.file_metadata.file_metadata_client.search_item',
        return_value={'result': {**item_info, 'extended': {'extra': {'tags': tags, 'attributes': attributes}}}},
    )
    httpx_mock.add_response(
        url=AppConfig.Connections.url_portal + f'/v1/data/manifest/{attri_template_uid}',
        method='GET',
        json={'result': {'id': attri_template_uid, 'name': attri_template_name}},
    )

    mocker.patch(
        'app.services.file_manager.file_metadata.file_metadata_client.FileMetaClient.save_file_metadata',
        return_value=None,
    )

    file_meta_client = FileMetaClient(
        'zone', f'{project_code}/{root_folder.get_prefix_by_type()}/{file_name}', 'general', 'attr', 'tag'
    )
    assert file_meta_client.project_code == project_code
    assert file_meta_client.object_path == f'{root_folder.get_prefix_by_type()}/{file_name}'

    item_info, res_attributes, tags = file_meta_client.download_file_metadata()
    assert item_info == item_info
    assert res_attributes == {attri_template_name: attributes.get(attri_template_uid)}
    assert tags == tags


@pytest.mark.parametrize(
    'root_folder',
    [ItemType.NAMEFOLDER, ItemType.SHAREDFOLDER],
)
def test_file_metadata_client_get_detail_success_with_no_tag_attributes(mocker, root_folder: ItemType):
    file_name = 'test_file.txt'
    project_code = 'project_code'
    item_info = {
        'id': 'test',
        'parent_id': 'test_parent',
        'parent_path': root_folder.get_prefix_by_type(),
        'name': file_name,
        'zone': 0,
        'status': 'ACTIVE',
        'container_code': project_code,
        'container_type': 'project',
    }

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    mocker.patch(
        'app.services.file_manager.file_metadata.file_metadata_client.search_item',
        return_value={'result': {**item_info, 'extended': {'extra': {'tags': [], 'attributes': {}}}}},
    )

    mocker.patch(
        'app.services.file_manager.file_metadata.file_metadata_client.FileMetaClient.save_file_metadata',
        return_value=None,
    )

    file_meta_client = FileMetaClient(
        'zone', f'{project_code}/{root_folder.get_prefix_by_type()}/{file_name}', 'general', 'attr', 'tag'
    )
    assert file_meta_client.project_code == project_code
    assert file_meta_client.object_path == f'{root_folder.get_prefix_by_type()}/{file_name}'

    item_info, res_attributes, tags = file_meta_client.download_file_metadata()
    assert item_info == item_info
    assert res_attributes == {}
    assert tags == tags


@pytest.mark.parametrize(
    'root_folder',
    [ItemType.NAMEFOLDER, ItemType.SHAREDFOLDER],
)
def test_metadata_download_fail_when_file_doesnot_exist(mocker, capfd, root_folder: ItemType):
    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    search_mock = mocker.patch(
        'app.services.file_manager.file_metadata.file_metadata_client.search_item',
        return_value={'result': {}, 'code': 404},
    )

    file_meta_client = FileMetaClient(
        'zone', f'project_code/{root_folder.get_prefix_by_type()}/file_name', 'general', 'attr', 'tag'
    )

    try:
        file_meta_client.download_file_metadata()
    except SystemExit:
        assert search_mock.call_count == 1
        out, _ = capfd.readouterr()

        expect = f'Cannot find item project_code/{root_folder.get_prefix_by_type()}/file_name at zone.\n'
        assert out == expect
    else:
        AssertionError('SystemExit not raised')
