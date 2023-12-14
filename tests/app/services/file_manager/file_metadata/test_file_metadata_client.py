# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from app.configs.app_config import AppConfig
from app.services.file_manager.file_metadata.file_metadata_client import FileMetaClient
from tests.conftest import decoded_token


def test_file_metadata_client_get_detail_success(mocker, httpx_mock):
    item_info = {
        'id': 'test',
        'parent_id': 'test_parent',
        'parent_path': '',
        'name': 'admin',
        'zone': 0,
        'status': 'ACTIVE',
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

    file_meta_client = FileMetaClient('zone', 'project_code/object_path', 'general', 'attr', 'tag')
    assert file_meta_client.project_code == 'project_code'
    assert file_meta_client.object_path == 'object_path'

    item_info, res_attributes, tags = file_meta_client.download_file_metadata()
    assert item_info == item_info
    assert res_attributes == {attri_template_name: attributes.get(attri_template_uid)}
    assert tags == tags


def test_file_metadata_client_get_detail_success_with_no_tag_attributes(mocker, httpx_mock):
    item_info = {
        'id': 'test',
        'parent_id': 'test_parent',
        'parent_path': '',
        'name': 'admin',
        'zone': 0,
        'status': 'ACTIVE',
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

    file_meta_client = FileMetaClient('zone', 'project_code/object_path', 'general', 'attr', 'tag')
    assert file_meta_client.project_code == 'project_code'
    assert file_meta_client.object_path == 'object_path'

    item_info, res_attributes, tags = file_meta_client.download_file_metadata()
    assert item_info == item_info
    assert res_attributes == {}
    assert tags == tags
