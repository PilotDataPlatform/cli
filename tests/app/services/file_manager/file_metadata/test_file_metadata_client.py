# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from app.services.file_manager.file_metadata.file_metadata_client import FileMetaClient


def test_file_metadata_client_get_detail_success(mocker):
    item_info = {
        'id': 'test',
        'parent_id': 'test_parent',
        'parent_path': '',
        'name': 'admin',
        'zone': 0,
        'status': 'ACTIVE',
    }
    tags = ['test']
    attributes = {'template_uid': {'attr_1': 'value'}}
    mocker.patch(
        'app.services.file_manager.file_metadata.file_metadata_client.search_item',
        return_value={'result': {**item_info, 'extended': {'extra': {'tags': tags, 'attributes': attributes}}}},
    )
    mocker.patch(
        'app.services.file_manager.file_metadata.file_metadata_client.FileMetaClient.save_file_metadata',
        return_value=None,
    )

    file_meta_client = FileMetaClient('zone', 'project_code/object_path', 'general', 'attr', 'tag')
    assert file_meta_client.project_code == 'project_code'
    assert file_meta_client.object_path == 'object_path'

    item_info, attributes, tags = file_meta_client.download_file_metadata()
    assert item_info == item_info
    assert attributes == attributes
    assert tags == tags
