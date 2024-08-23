# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from unittest.mock import Mock

import questionary

from app.commands.dataset import dataset_download
from app.commands.dataset import dataset_list
from app.configs.app_config import AppConfig


def list_fake_dataset(number: int):
    return [f'dataset-{i}' for i in range(number)]


def test_dataset_list_total_less_than_10(httpx_mock, mocker, cli_runner, capsys):
    page_size = 10
    project_list = list_fake_dataset(5)
    mocker.patch(
        'app.services.dataset_manager.dataset_list.SrvDatasetListManager.list_datasets', return_value=project_list
    )

    result = cli_runner.invoke(dataset_list, ['--page', 0, '--page-size', page_size])

    assert result.exit_code == 0
    assert '' == result.output


def test_dataset_list_total_more_than_10_page_0(httpx_mock, mocker, cli_runner, capsys):
    page_size = 10
    project_list = list_fake_dataset(20)
    mocker.patch(
        'app.services.dataset_manager.dataset_list.SrvDatasetListManager.list_datasets', return_value=project_list
    )
    clear_mock = mocker.patch('click.clear', return_value=None)

    question_mock = mocker.patch.object(questionary, 'select', return_value=questionary.select)
    questionary.select.return_value.ask = Mock()
    questionary.select.return_value.ask.side_effect = ['next page', 'previous page', 'exit']

    result = cli_runner.invoke(dataset_list, ['--page', 0, '--page-size', page_size])

    assert result.exit_code == 0
    assert question_mock.call_count == 3
    assert clear_mock.call_count == 2


def test_download_not_exited_dataset_version(httpx_mock, mocker, cli_runner, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    httpx_mock.add_response(
        method='GET',
        url='http://bff_cli/v1/dataset/testdataset?page=0&page_size=500',
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

    httpx_mock.add_response(
        method='POST',
        url=AppConfig.Connections.url_dataset + '/fake-id/download/pre/version/1.0',
        json={'error': 'version does not exist'},
        status_code=500,
    )

    result = cli_runner.invoke(dataset_download, ['testdataset', '.', '-v', '1.0'])
    outputs = result.output.split('\n')
    assert outputs[0] == 'Target dataset version: 1.0'
    assert outputs[1] == 'Version not available: 1.0'
