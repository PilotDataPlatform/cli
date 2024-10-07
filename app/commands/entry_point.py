# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import click

from app.services.user_authentication.decorator import require_config
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
from .file import file_put
from .file import file_resume
from .project import project_list_all
from .use_config import set_env
from .user import login
from .user import logout


def command_groups():
    commands = ['file', 'user', 'use_config', 'project', 'dataset', 'container_registry']
    return commands


@click.group()
def entry_point():
    pass


@entry_point.group(name='project')
@require_config
@require_login_session
def project_group():
    pass


@entry_point.group(name='dataset')
@require_config
@require_login_session
def dataset_group():
    pass


@entry_point.group(name='file')
@require_config
@require_login_session
def file_group():
    pass


@entry_point.group(name='user')
@require_config
def user_group():
    pass


@entry_point.group(name='use_config')
def config_group():
    pass


@entry_point.group(name='container_registry')
@require_config
def cr_group():
    pass


file_group.add_command(file_put)
file_group.add_command(file_check_manifest)
file_group.add_command(file_export_manifest)
file_group.add_command(file_list)
file_group.add_command(file_download)
file_group.add_command(file_resume)
project_group.add_command(project_list_all)
user_group.add_command(login)
user_group.add_command(logout)
dataset_group.add_command(dataset_list)
dataset_group.add_command(dataset_show_detail)
dataset_group.add_command(dataset_download)
cr_group.add_command(list_projects)
cr_group.add_command(list_repositories)
cr_group.add_command(create_project)
cr_group.add_command(get_secret)
cr_group.add_command(invite_member)
config_group.add_command(set_env)
