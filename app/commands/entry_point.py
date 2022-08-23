# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

import click

from app.services.user_authentication.decorator import require_login_session
from app.services.user_authentication.decorator import require_config

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

# Import custom commands
from .hpc import hpc_auth
from .hpc import hpc_get_node
from .hpc import hpc_get_partition
from .hpc import hpc_job_info
from .hpc import hpc_job_submit
from .hpc import hpc_list_nodes
from .hpc import hpc_list_partitions
from .kg_resource import kg_resource
from .project import project_list_all
from .user import login
from .user import logout
from .use_config import set_env

hpc_enabled = os.environ.get('PILOT_CLI_HPC_ENABLED', 'false') == 'true'
kg_enabled = os.environ.get('PILOT_CLI_KG_ENABLED', 'false') == 'true'


def command_groups():
    commands = ['file', 'user', 'use_config', 'project', 'dataset', 'container_registry']
    if hpc_enabled:
        commands.append('hpc')
    if kg_enabled:
        commands.append('kg_resource')
    return commands


@click.group()
def entry_point():
    pass


@entry_point.group(name="project")
@require_config
@require_login_session
def project_group():
    pass


@entry_point.group(name="dataset")
@require_config
@require_login_session
def dataset_group():
    pass


@entry_point.group(name="file")
@require_config
@require_login_session
def file_group():
    pass


@entry_point.group(name="user")
@require_config
def user_group():
    pass

@entry_point.group(name="use_config")
def config_group():
    pass

@entry_point.group(name="container_registry")
@require_config
def cr_group():
    pass


file_group.add_command(file_put)
file_group.add_command(file_check_manifest)
file_group.add_command(file_export_manifest)
file_group.add_command(file_list)
file_group.add_command(file_download)
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

# Custom commands
if hpc_enabled:
    @entry_point.group(name="hpc")
    def hpc_group():
        pass

    hpc_group.add_command(hpc_auth)
    hpc_group.add_command(hpc_job_submit)
    hpc_group.add_command(hpc_job_info)
    hpc_group.add_command(hpc_list_nodes)
    hpc_group.add_command(hpc_get_node)
    hpc_group.add_command(hpc_list_partitions)
    hpc_group.add_command(hpc_get_partition)

if kg_enabled:
    @entry_point.group(name="kg_resource")
    def kg_resource_group():
        pass

    kg_resource_group.add_command(kg_resource)
