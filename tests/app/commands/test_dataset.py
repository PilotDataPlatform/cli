# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from unittest.mock import Mock

import pytest
import questionary

from app.commands.dataset import dataset_download
from app.commands.dataset import dataset_list
from app.commands.dataset import dataset_show_detail
from app.configs.app_config import AppConfig


def list_fake_dataset(number: int):
    return [f'dataset-{i}' for i in range(number)]


def list_fake_dataset_version(number: int):
    return [f'dataset-{i}' for i in range(number)]


def test_dataset_list_total_less_than_10(mocker, cli_runner):
    page_size = 10
    fake_list = list_fake_dataset(5)
    mocker.patch(
        'app.services.dataset_manager.dataset_list.SrvDatasetListManager.list_datasets',
        return_value=(fake_list, len(fake_list)),
    )
    question_mock = mocker.patch.object(questionary, 'select', return_value=questionary.select)

    result = cli_runner.invoke(dataset_list, ['--page', 0, '--page-size', page_size])

    assert result.exit_code == 0
    assert '' == result.output
    assert question_mock.call_count == 0


@pytest.mark.parametrize(
    'page, options',
    [(0, ['next page', 'exit']), (1, ['next page', 'previous page', 'exit']), (2, ['previous page', 'exit'])],
)
def test_dataset_list_total_more_than_10(mocker, cli_runner, page, options):
    page_size = 9
    fake_list = list_fake_dataset(20)
    mocker.patch(
        'app.services.dataset_manager.dataset_list.SrvDatasetListManager.list_datasets',
        return_value=(fake_list, len(fake_list)),
    )
    clear_mock = mocker.patch('click.clear', return_value=None)

    question_mock = mocker.patch.object(questionary, 'select', return_value=questionary.select)
    questionary.select.return_value.ask = Mock()
    questionary.select.return_value.ask.side_effect = options

    result = cli_runner.invoke(dataset_list, ['--page', page, '--page-size', page_size])

    assert result.exit_code == 0
    assert question_mock.call_count == len(options)
    assert clear_mock.call_count == len(options) - 1


def test_dataset_show_detail_with_version_less_than_10(httpx_mock, mocker, cli_runner, capsys):
    fake_list = list_fake_dataset_version(5)
    fake_detail = {
        'general_info': {
            'title': 'test dataset',
            'code': 'testdataset',
        },
        'version_detail': fake_list,
        'version_no': len(fake_list),
    }
    mocker.patch(
        'app.services.dataset_manager.dataset_detail.SrvDatasetDetailManager.dataset_detail', return_value=fake_detail
    )
    question_mock = mocker.patch.object(questionary, 'select', return_value=questionary.select)

    result = cli_runner.invoke(dataset_show_detail, ['testdataset'])

    assert result.exit_code == 0
    assert '' == result.output
    assert question_mock.call_count == 0


@pytest.mark.parametrize(
    'page, options',
    [(0, ['next page', 'exit']), (1, ['next page', 'previous page', 'exit']), (2, ['previous page', 'exit'])],
)
def test_dataset_show_detail_with_version_more_than_10(mocker, cli_runner, page, options):
    page_size = 9
    fake_list = list_fake_dataset_version(20)
    fake_detail = {
        'general_info': {
            'title': 'test dataset',
            'code': 'testdataset',
        },
        'version_detail': fake_list,
        'version_no': len(fake_list),
    }
    mocker.patch(
        'app.services.dataset_manager.dataset_detail.SrvDatasetDetailManager.dataset_detail', return_value=fake_detail
    )
    clear_mock = mocker.patch('click.clear', return_value=None)

    question_mock = mocker.patch.object(questionary, 'select', return_value=questionary.select)
    questionary.select.return_value.ask = Mock()
    questionary.select.return_value.ask.side_effect = options

    result = cli_runner.invoke(dataset_show_detail, ['testdataset', '--page', page, '--page-size', page_size])

    assert result.exit_code == 0
    assert question_mock.call_count == len(options)
    assert clear_mock.call_count == len(options) - 1


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
