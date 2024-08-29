# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pytest

from app.commands.folder import folder_create
from app.configs.app_config import AppConfig


@pytest.mark.parametrize('zone', [AppConfig.Env.green_zone, AppConfig.Env.core_zone])
def test_folder_create_success(mocker, cli_runner, zone):
    project_code = 'testproject'
    object_path = 'users/testuser/testfolder'

    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    mocker.patch('app.services.file_manager.file_metadata.folder_client.FolderClient.create_folder', return_value={})

    result = cli_runner.invoke(folder_create, [f'{project_code}/{object_path}', '-z', zone])
    assert result.exit_code == 0
    assert f'Folder created: {object_path} at project: {project_code} at zone: {zone}' in result.output


def test_folder_create_invalid_folder_path(mocker, cli_runner):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    mocker.patch('app.services.file_manager.file_metadata.folder_client.FolderClient.create_folder', return_value={})

    result = cli_runner.invoke(folder_create, ['testproject/users/testuser'])
    assert result.exit_code == 1
    assert 'Invalid folder path' in result.output


# test [/:?.\\*<>|”\']
@pytest.mark.parametrize('invalid_char', [r'\\', '/', ':', '?', '.', '\'', '*', '<', '>', '|', '”'])
def test_folder_create_invalid_folder_name(mocker, cli_runner, invalid_char):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    mocker.patch('app.services.file_manager.file_metadata.folder_client.FolderClient.create_folder', return_value={})

    result = cli_runner.invoke(folder_create, [f'testproject/users/testuser/testfolder{invalid_char}'])

    assert result.exit_code == 1
    assert 'The input folder name is not valid. Please follow the rule:' in result.output
