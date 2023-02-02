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
import questionary

import app.services.output_manager.help_page as project_help
import app.services.output_manager.message_handler as mhandler
from app.services.project_manager.project import SrvProjectManager
from app.utils.aggregated import doc


@click.command()
def cli():
    """Project Actions"""
    pass


@click.command(name="list")
@click.option('--page',
              default=0,
              required=False,
              help=' The page to be listed',
              show_default=True)
@click.option('--page-size',
              default=10,
              required=False,
              help='number of objects per page',
              show_default=True)
@click.option('--order',
              default='desc',
              required=False,
              type=click.Choice(['asc', 'desc']),
              help='sorting order',
              show_default=True)
@click.option('--order-by',
              default='created_at',
              required=False,
              type=click.Choice(['created_at', 'name', 'code']),
              help='sorting column',
              show_default=True)
@click.option('-d', '--detached',
              default=None,
              required=False,
              is_flag=True,
              help='whether run in detached mode',
              show_default=True)
@doc(project_help.project_help_page(project_help.ProjectHELP.PROJECT_LIST))
def project_list_all(page, page_size, order, order_by, detached):
    if detached:
        project_mgr = SrvProjectManager()
        projects = project_mgr.list_projects(page, page_size, order, order_by)
    else:
        while True:
            project_mgr = SrvProjectManager()
            projects = project_mgr.list_projects(page, page_size, order, order_by)
            if len(projects) < page_size and page == 0:
                break
            elif len(projects) < page_size and page != 0:
                choice = ['previous page', 'exit']
            elif page == 0:
                choice = ['next page', 'exit']
            else:
                choice = ['previous page', 'next page', 'exit']
            val = questionary.select(
                "\nWhat do you want?",
                qmark="",
                choices=choice).ask()
            if val == 'exit':
                mhandler.SrvOutPutHandler.list_success('Project')
                break
            elif val == 'next page':
                click.clear()
                page += 1
            elif val == 'previous page':
                click.clear()
                page -= 1
