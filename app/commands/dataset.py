# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import click
import questionary

import app.services.output_manager.help_page as dataset_help
import app.services.output_manager.message_handler as message_handler
from app.services.dataset_manager.dataset_detail import SrvDatasetDetailManager
from app.services.dataset_manager.dataset_download import SrvDatasetDownloadManager
from app.services.dataset_manager.dataset_list import SrvDatasetListManager
from app.utils.aggregated import doc


@click.command()
def cli():
    """Dataset Actions."""
    pass


@click.command(name='list')
@click.option(
    '--all',
    'all_considering_admin_role',
    default=False,
    required=False,
    is_flag=True,
    help='Show also datasets that belong to projects where user has admin role',
)
@click.option('--page', default=0, required=False, help=' The page to be listed', show_default=True)
@click.option('--page-size', default=10, required=False, help='number of objects per page', show_default=True)
@click.option(
    '-d',
    '--detached',
    default=None,
    required=False,
    is_flag=True,
    help='whether run in detached mode',
    show_default=True,
)
@doc(dataset_help.dataset_help_page(dataset_help.DatasetHELP.DATASET_LIST))
def dataset_list(all_considering_admin_role, page, page_size, detached):
    filter_by_creator = not all_considering_admin_role
    if detached:
        dataset_mgr = SrvDatasetListManager()
        datasets = dataset_mgr.list_datasets(page, page_size, filter_by_creator)
    else:
        while True:
            dataset_mgr = SrvDatasetListManager()
            datasets = dataset_mgr.list_datasets(page, page_size, filter_by_creator)
            if len(datasets) < page_size and page == 0:
                break
            elif len(datasets) < page_size and page != 0:
                choice = ['previous page', 'exit']
            elif page == 0:
                choice = ['next page', 'exit']
            else:
                choice = ['previous page', 'next page', 'exit']
            val = questionary.select('\nWhat do you want?', qmark='', choices=choice).ask()
            if val == 'exit':
                message_handler.SrvOutPutHandler.list_success('Dataset')
                break
            elif val == 'next page':
                click.clear()
                page += 1
            elif val == 'previous page':
                click.clear()
                page -= 1


@click.command(name='show-detail')
@click.argument('code', type=click.STRING, nargs=1)
@click.option('--page', default=0, required=False, help=' The page to be listed', show_default=True)
@click.option('--page-size', default=10, required=False, help='number of objects per page', show_default=True)
@click.option(
    '-d',
    '--detached',
    default=None,
    required=False,
    is_flag=True,
    help='whether run in detached mode',
    show_default=True,
)
@doc(dataset_help.dataset_help_page(dataset_help.DatasetHELP.DATASET_SHOW_DETAIL))
def dataset_show_detail(code, page, page_size, detached):
    if detached:
        detail_mgr = SrvDatasetDetailManager()
        detail_mgr.dataset_detail(code, page, page_size)
    else:
        while True:
            detail_mgr = SrvDatasetDetailManager()
            detail_info = detail_mgr.dataset_detail(code, page, page_size)
            versions = detail_info.get('version_detail')
            if len(versions) < page_size and page == 0:
                break
            if len(versions) < page_size and page != 0:
                choice = ['previous page', 'exit']
            elif page == 0:
                choice = ['next page', 'exit']
            else:
                choice = ['previous page', 'next page', 'exit']
            val = questionary.select('\nWhat do you want?', qmark='', choices=choice).ask()
            if val == 'exit':
                message_handler.SrvOutPutHandler.list_success('Dataset')
                break
            elif val == 'next page':
                click.clear()
                page += 1
            elif val == 'previous page':
                click.clear()
                page -= 1


@click.command(name='download')
@click.argument('code', type=click.STRING, nargs=-1)
@click.argument('output_path', type=click.Path(exists=True), nargs=1)
@click.option(
    '-v',
    '--version',
    default=None,
    required=False,
    help=dataset_help.dataset_help_page(dataset_help.DatasetHELP.DATASET_VERSION),
    show_default=True,
)
@doc(dataset_help.dataset_help_page(dataset_help.DatasetHELP.DATASET_DOWNLOAD))
def dataset_download(code, output_path, version):
    srv_detail = SrvDatasetDetailManager(interactive=False)
    for dataset_code in code:
        dataset_info = srv_detail.dataset_detail(dataset_code, page=0, page_size=500)
        if not dataset_info:
            continue
        dataset_geid = dataset_info.get('general_info').get('id')
        srv_download = SrvDatasetDownloadManager(output_path, dataset_code, dataset_geid)
        if not version:
            srv_download.download_dataset()
        else:
            message_handler.SrvOutPutHandler.dataset_current_version(version)
            srv_download.download_dataset_version(version)
