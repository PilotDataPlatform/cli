# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

from app.commands.dataset import dataset_download
from app.configs.app_config import AppConfig


def test_file_upload_command_success_with_attribute(requests_mock, mocker, cli_runner, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    requests_mock.get(
        'http://bff_cli' + '/v1/dataset/testdataset',
        json={
            'code': 200,
            'error_msg': '',
            'result': {
                'general_info': {
                    'id': 'fake-id',
                    'source': '',
                    'authors': ['test-admin', 'test-user'],
                    'code': 'testdataset',
                    'type': 'GENERAL',
                    'modality': [],
                    'collection_method': [],
                    'license': '',
                    'tags': ['cdsa'],
                    'description': 'Description example.',
                    'size': 25,
                    'total_files': 1,
                    'title': 'test dataset',
                    'creator': 'test-admin',
                    'project_id': 'project-id',
                    'created_at': '2022-02-03T19:49:35',
                    'updated_at': '2022-03-18T18:08:33',
                },
                'version_detail': [],
                'version_no': 0,
            },
        },
    )

    requests_mock.get(
        AppConfig.Connections.url_dataset + '/fake-id/download/pre',
        json={'error': 'version does not exist'},
        status_code=404,
    )

    result = cli_runner.invoke(dataset_download, ['testdataset', '.', '-v', '1.0'])
    outputs = result.output.split('\n')
    assert outputs[0] == 'Current dataset version: 1.0'
    assert outputs[1] == 'Version not available: 1.0'
