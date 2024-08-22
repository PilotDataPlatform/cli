# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import click
import questionary

import app.services.output_manager.help_page as project_help
import app.services.output_manager.message_handler as mhandler
from app.configs.app_config import AppConfig
from app.services.project_manager.project import SrvProjectManager
from app.utils.aggregated import doc


@click.command()
def cli():
    """Project Actions."""
    pass


@click.command(name='list')
@click.option('--page', default=0, required=False, help=' The page to be listed', show_default=True)
@click.option('--page-size', default=10, required=False, help='number of objects per page', show_default=True)
@click.option(
    '--order',
    default='desc',
    required=False,
    type=click.Choice(['asc', 'desc']),
    help='sorting order',
    show_default=True,
)
@click.option(
    '--order-by',
    default='created_at',
    required=False,
    type=click.Choice(['created_at', 'name', 'code']),
    help='sorting column',
    show_default=True,
)
@click.option(
    '-d',
    '--detached',
    default=None,
    required=False,
    is_flag=True,
    help='whether run in detached mode',
    show_default=True,
)
@doc(project_help.project_help_page(project_help.ProjectHELP.PROJECT_LIST))
def project_list_all(page, page_size, order, order_by, detached):
    project_mgr = SrvProjectManager()

    if detached:
        projects = project_mgr.list_projects(page, page_size, order, order_by)
    else:
        while True:
            projects = project_mgr.list_projects(page, page_size, order, order_by)
            if len(projects) < AppConfig.Env.interative_threshold:
                break
            elif page == 0:
                choice = ['next page', 'exit']
            else:
                choice = ['previous page', 'next page', 'exit']

            val = questionary.select('\nWhat do you want?', qmark='', choices=choice).ask()
            if val == 'exit':
                mhandler.SrvOutPutHandler.list_success('Project')
                break
            elif val == 'next page':
                click.clear()
                page += 1
            elif val == 'previous page':
                click.clear()
                page -= 1
