# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

from app.commands.dataset import dataset_download
from app.commands.dataset import dataset_list
from app.commands.dataset import dataset_show_detail
from app.commands.entry_point import command_groups
from app.commands.entry_point import entry_point
from app.commands.file import file_check_manifest
from app.commands.file import file_download
from app.commands.file import file_export_manifest
from app.commands.file import file_list
from app.commands.file import file_put
from app.commands.file import file_resume
from app.commands.project import project_list_all
from app.commands.user import login
from app.commands.user import logout


def test_entry_point():
    possible_commands = command_groups()

    for x in possible_commands:
        assert x in entry_point.commands.keys()


def test_project_commands():
    assert 'project' in entry_point.commands.keys()

    func_map = {
        'list': project_list_all,
    }
    project_commands_object = entry_point.commands.get('project')

    for x in project_commands_object.commands.keys():
        assert func_map.get(x) == project_commands_object.commands.get(x)


def test_user_commands():
    assert 'user' in entry_point.commands.keys()

    func_map = {
        'login': login,
        'logout': logout,
    }
    user_commands_object = entry_point.commands.get('user')

    for x in user_commands_object.commands.keys():
        assert func_map.get(x) == user_commands_object.commands.get(x)


def test_file_commands():
    assert 'file' in entry_point.commands.keys()

    func_map = {
        'list': file_list,
        'upload': file_put,
        'attribute-list': file_check_manifest,
        'attribute-export': file_export_manifest,
        'sync': file_download,
        'resume': file_resume,
    }
    file_commands_object = entry_point.commands.get('file')

    for x in file_commands_object.commands.keys():
        assert func_map.get(x) == file_commands_object.commands.get(x)


def test_dataset_commands():
    assert 'dataset' in entry_point.commands.keys()

    func_map = {
        'list': dataset_list,
        'show-detail': dataset_show_detail,
        'download': dataset_download,
    }
    dataset_commands_object = entry_point.commands.get('dataset')

    for x in dataset_commands_object.commands.keys():
        assert func_map.get(x) == dataset_commands_object.commands.get(x)
