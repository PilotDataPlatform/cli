# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import click

import app.services.output_manager.help_page as help_page
from app.services.container_registry_manager.container_registry_manager import SrvContainerRegistryMgr
from app.services.output_manager.message_handler import SrvOutPutHandler
from app.utils.aggregated import doc


@click.command()
def cli():
    """Container Registry Actions."""
    pass


@click.command()
@doc(help_page.cr_help_page(help_page.ContainerRegistryHELP.LIST_PROJECTS))
def list_projects():
    manager = SrvContainerRegistryMgr()
    project_names = manager.get_all_projects()
    SrvOutPutHandler.print_container_registry_project_list(project_names)


@click.command()
@click.option('-p', '--project', required=False, default=None)
@doc(help_page.cr_help_page(help_page.ContainerRegistryHELP.LIST_REPOSITORIES))
def list_repositories(project):
    manager = SrvContainerRegistryMgr()
    repo_names = manager.get_all_repos(project)
    SrvOutPutHandler.print_container_registry_repo_list(repo_names, project)


@click.command()
@click.option('-n', '--name', prompt='Project name')
@click.option('-v', '--visibility', prompt='Project visibility (public | private)')
@doc(help_page.cr_help_page(help_page.ContainerRegistryHELP.CREATE_PROJECT))
def create_project(name, visibility):
    manager = SrvContainerRegistryMgr()
    success = manager.create_project(name, visibility)
    if success:
        SrvOutPutHandler.container_registry_create_project_success(name)


@click.command()
@doc(help_page.cr_help_page(help_page.ContainerRegistryHELP.GET_SECRET))
def get_secret():
    manager = SrvContainerRegistryMgr()
    secret = manager.get_current_user_secret()
    if secret:
        SrvOutPutHandler.container_registry_get_secret_success(secret)


@click.command()
@click.option('-r', '--role', prompt='Role for shared user (admin | developer | guest | maintainer)')
@click.option('-p', '--project', prompt='Project name')
@click.option('-u', '--username', prompt='Username of shared user')
@doc(help_page.cr_help_page(help_page.ContainerRegistryHELP.SHARE_PROJECT))
def invite_member(role, project, username):
    manager = SrvContainerRegistryMgr()
    success = manager.share_project(role, project, username)
    if success:
        SrvOutPutHandler.container_registry_share_project_success(role, project, username)
