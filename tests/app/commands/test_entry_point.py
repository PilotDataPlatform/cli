# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from app.commands.dataset import dataset_download
from app.commands.dataset import dataset_list
from app.commands.dataset import dataset_show_detail
from app.commands.entry_point import command_groups
from app.commands.entry_point import entry_point
from app.commands.file import file_check_manifest
from app.commands.file import file_download
from app.commands.file import file_export_manifest
from app.commands.file import file_list
from app.commands.file import file_metadata_download
from app.commands.file import file_move
from app.commands.file import file_put
from app.commands.file import file_resume
from app.commands.file import file_trash
from app.commands.project import project_list_all
from app.commands.user import login
from app.commands.user import logout


def test_entry_point():
    possible_commands = command_groups()

    for x in possible_commands:
        assert x in entry_point.commands.keys()


def test_project_commands(user_login_true):
    assert 'project' in entry_point.commands.keys()

    func_map = {
        'list': project_list_all,
    }
    project_commands_object = entry_point.commands.get('project')
    project_commands_object.callback()

    for x in project_commands_object.commands.keys():
        assert func_map.get(x) == project_commands_object.commands.get(x)


def test_user_commands(user_login_true):
    assert 'user' in entry_point.commands.keys()

    func_map = {
        'login': login,
        'logout': logout,
    }
    user_commands_object = entry_point.commands.get('user')
    user_commands_object.callback()

    for x in user_commands_object.commands.keys():
        assert func_map.get(x) == user_commands_object.commands.get(x)


def test_file_commands(user_login_true):
    assert 'file' in entry_point.commands.keys()

    func_map = {
        'list': file_list,
        'upload': file_put,
        'attribute-list': file_check_manifest,
        'attribute-export': file_export_manifest,
        'download': file_download,
        'resume': file_resume,
        'metadata': file_metadata_download,
        'move': file_move,
        'trash': file_trash,
    }
    file_commands_object = entry_point.commands.get('file')
    file_commands_object.callback()

    for x in file_commands_object.commands.keys():
        assert func_map.get(x) == file_commands_object.commands.get(x)


def test_dataset_commands(user_login_true):
    assert 'dataset' in entry_point.commands.keys()

    func_map = {
        'list': dataset_list,
        'show-detail': dataset_show_detail,
        'download': dataset_download,
    }
    dataset_commands_object = entry_point.commands.get('dataset')
    dataset_commands_object.callback()

    for x in dataset_commands_object.commands.keys():
        assert func_map.get(x) == dataset_commands_object.commands.get(x)
