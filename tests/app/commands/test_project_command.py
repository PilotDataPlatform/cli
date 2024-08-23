# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from unittest.mock import Mock

import pytest
import questionary

from app.commands.project import project_list_all


def list_fake_project(number: int):
    return [f'project-{i}' for i in range(number)]


def test_list_project_is_smaller_than_page_size(mocker, cli_runner):
    page_size = 10
    project_list = list_fake_project(5)
    mocker.patch(
        'app.services.project_manager.project.SrvProjectManager.list_projects',
        return_value=(project_list, len(project_list)),
    )
    question_mock = mocker.patch.object(questionary, 'select', return_value=questionary.select)

    result = cli_runner.invoke(
        project_list_all, ['--page', 0, '--page-size', page_size, '--order', 'desc', '--order-by', 'created_at']
    )

    assert result.exit_code == 0
    assert '' == result.output
    assert question_mock.call_count == 0


@pytest.mark.parametrize(
    'page, options',
    [(0, ['next page', 'exit']), (1, ['next page', 'previous page', 'exit']), (2, ['previous page', 'exit'])],
)
def test_list_project_is_larger_than_10(mocker, cli_runner, page, options):
    page_size = 9
    project_list = list_fake_project(20)
    mocker.patch(
        'app.services.project_manager.project.SrvProjectManager.list_projects',
        return_value=(project_list, len(project_list)),
    )
    clear_mock = mocker.patch('click.clear', return_value=None)

    question_mock = mocker.patch.object(questionary, 'select', return_value=questionary.select)
    questionary.select.return_value.ask = Mock()
    questionary.select.return_value.ask.side_effect = options

    result = cli_runner.invoke(
        project_list_all, ['--page', 0, '--page-size', page_size, '--order', 'desc', '--order-by', 'created_at']
    )

    assert result.exit_code == 0
    assert 'Project list fetched successfully!\n' == result.output
    assert question_mock.call_count == len(options)
    assert clear_mock.call_count == len(options) - 1


def test_list_project_with_detached(mocker, cli_runner):
    page_size = 10
    project_list = list_fake_project(10)
    mocker.patch(
        'app.services.project_manager.project.SrvProjectManager.list_projects',
        return_value=(project_list, len(project_list)),
    )

    clear_mock = mocker.patch('click.clear', return_value=None)
    question_mock = mocker.patch.object(questionary, 'select', return_value=questionary.select)

    result = cli_runner.invoke(
        project_list_all,
        ['--page', 0, '--page-size', page_size, '--order', 'desc', '--order-by', 'created_at', '--detached'],
    )

    assert result.exit_code == 0
    assert '' == result.output
    assert question_mock.call_count == 0
    assert clear_mock.call_count == 0
