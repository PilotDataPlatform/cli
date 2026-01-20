# Copyright (C) 2022-2026 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import os

import click

from app.services.user_authentication.decorator import require_login_session

from .container_registry import create_project, get_secret, invite_member, list_projects, list_repositories
from .dataset import dataset_download, dataset_list, dataset_show_detail
from .file import (
    file_check_manifest,
    file_download,
    file_export_manifest,
    file_list,
    file_metadata_download,
    file_move,
    file_put,
    file_resume,
    file_trash,
)
from .folder import folder_create

# Import custom commands
from .project import project_list_all
from .user import login, logout

container_registry_enabled = os.environ.get('PILOT_CLI_CONTAINER_REGISTRY_ENABLED', 'false') == 'true'


def command_groups():
    commands = ['file', 'user', 'project', 'dataset', 'folder']
    if container_registry_enabled:
        commands.append('container_registry')
    return commands


@click.group()
def entry_point():
    pass


@entry_point.group(name='project')
@require_login_session
def project_group():
    pass


@entry_point.group(name='dataset')
@require_login_session
def dataset_group():
    pass


@entry_point.group(name='file')
@require_login_session
def file_group():
    pass


@entry_point.group(name='user')
def user_group():
    pass


@entry_point.group(name='folder')
def folder_group():
    pass


file_group.add_command(file_put)
file_group.add_command(file_check_manifest)
file_group.add_command(file_export_manifest)
file_group.add_command(file_list)
file_group.add_command(file_download)
file_group.add_command(file_resume)
file_group.add_command(file_metadata_download)
file_group.add_command(file_move)
file_group.add_command(file_trash)
project_group.add_command(project_list_all)
user_group.add_command(login)
user_group.add_command(logout)
dataset_group.add_command(dataset_list)
dataset_group.add_command(dataset_show_detail)
dataset_group.add_command(dataset_download)
folder_group.add_command(folder_create)

# Custom commands
if container_registry_enabled:

    @entry_point.group(name='container_registry')
    def cr_group():
        pass

    cr_group.add_command(list_projects)
    cr_group.add_command(list_repositories)
    cr_group.add_command(create_project)
    cr_group.add_command(get_secret)
    cr_group.add_command(invite_member)
