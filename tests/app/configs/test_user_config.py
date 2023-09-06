# Copyright (C) 2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import os
import stat
import sys

import pytest

from app.configs.user_config import UserConfig


@pytest.fixture
def error_log(mocker):
    return mocker.patch('app.services.logger_services.log_functions.error')


class TestUserConfig:
    def test__init__creates_config_folder_with_0700_and_file_with_0600_access_modes(self, tmp_path, fake):
        config_folder = tmp_path / fake.pystr()
        file_name = fake.pystr()

        UserConfig(config_folder, file_name)

        config_folder_mode = stat.S_IMODE(config_folder.stat().st_mode)
        assert config_folder_mode == 0o0700

        config_file_mode = stat.S_IMODE((config_folder / file_name).stat().st_mode)
        assert config_file_mode == 0o0600

    def test__init__exits_with_error_when_config_folder_does_not_belong_to_user(self, error_log):
        with pytest.raises(SystemExit):
            UserConfig('/')

        expected_message = (
            'Cannot proceed with current config permissions.\n'
            f'"/" is owned by the user id 0. Expected user id is {os.geteuid()}.'
        )

        error_log.assert_called_with(expected_message)

    def test__init__exits_with_error_when_config_folder_does_not_have_expected_access_mode(
        self, error_log, tmp_path, fake
    ):
        config_folder = tmp_path / fake.pystr()
        config_folder.mkdir(mode=0o0755)

        with pytest.raises(SystemExit):
            UserConfig(config_folder)

        expected_message = (
            'Cannot proceed with current config permissions.\n'
            f'Permissions 755 for "{config_folder}" are too open. Expected permissions are 500, 700.'
        )

        error_log.assert_called_with(expected_message)

    def test__init__exits_with_error_when_config_file_does_not_have_expected_access_mode(
        self, error_log, tmp_path, fake
    ):
        config_folder = tmp_path / fake.pystr()
        file_name = fake.pystr()
        config_file = config_folder / file_name
        config_folder.mkdir(mode=0o0700)
        config_file.touch(mode=0o0644)

        with pytest.raises(SystemExit):
            UserConfig(config_folder, file_name)

        expected_message = (
            'Cannot proceed with current config permissions.\n'
            f'Permissions 644 for "{config_file}" are too open. Expected permissions are 400, 600.'
        )

        error_log.assert_called_with(expected_message)

    def test__init__does_not_exit_with_error_when_config_folder_has_invalid_access_mode_and_is_cloud_mode_set_to_true(
        self, tmp_path, fake
    ):
        config_folder = tmp_path / fake.pystr()
        config_folder.mkdir(mode=0o0755)

        UserConfig(config_folder, is_cloud_mode=True)

    def test__init__does_not_exit_with_error_when_config_file_has_invalid_access_mode_and_is_cloud_mode_set_to_true(
        self, tmp_path, fake
    ):
        config_folder = tmp_path / fake.pystr()
        file_name = fake.pystr()
        config_file = config_folder / file_name
        config_folder.mkdir(mode=0o0700)
        config_file.touch(mode=0o0644)

        UserConfig(config_folder, file_name, is_cloud_mode=True)

    def test__init__sets_is_cloud_mode_to_false_by_default(self, tmp_path, fake):
        config_folder = tmp_path / fake.pystr()

        user_config = UserConfig(config_folder)

        assert user_config.is_cloud_mode is False

    def test__init__sets_is_cloud_mode_to_true_when_pyinstaller_bundle_params_are_set_and_cloud_mode_file_is_present(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr(sys, 'frozen', True, raising=False)
        monkeypatch.setattr(sys, '_MEIPASS', str(tmp_path), raising=False)

        cloud_mode_file = tmp_path / 'ENABLE_CLOUD_MODE'
        cloud_mode_file.touch()

        user_config = UserConfig()

        assert user_config.is_cloud_mode is True
