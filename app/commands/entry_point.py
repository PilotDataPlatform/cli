# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import os

import click

from app.services.user_authentication.decorator import require_login_session

from .container_registry import create_project
from .container_registry import get_secret
from .container_registry import invite_member
from .container_registry import list_projects
from .container_registry import list_repositories
from .dataset import dataset_download
from .dataset import dataset_list
from .dataset import dataset_show_detail
from .file import file_check_manifest
from .file import file_download
from .file import file_export_manifest
from .file import file_list
from .file import file_metadata_download
from .file import file_move
from .file import file_put
from .file import file_resume
from .file import file_trash
from .folder import folder_create

# Import custom commands
from .project import project_list_all
from .user import login
from .user import logout

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
