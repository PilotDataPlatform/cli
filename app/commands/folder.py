# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import click

from app.configs.app_config import AppConfig
from app.services.file_manager.file_metadata.folder_client import FolderClient
from app.services.output_manager.help_page import FileHELP
from app.services.output_manager.help_page import FolderHelp
from app.services.output_manager.help_page import file_help_page
from app.services.output_manager.help_page import folder_help_page
from app.utils.aggregated import doc


@click.command()
def cli():
    """folder Actions."""
    pass


@click.command(name='create')
@click.argument('project_code', type=str)
@click.argument('object_path', type=str)
@click.option(
    '-z',
    '--zone',
    type=click.Choice([AppConfig.Env.green_zone, AppConfig.Env.core_zone]),
    default=AppConfig.Env.green_zone,
    required=False,
    help=file_help_page(FileHELP.FILE_Z),
    show_default=True,
)
@doc(folder_help_page(FolderHelp.FOLDER_CREATE))
def folder_create(project_code, object_path, zone):
    """"""

    if len(object_path.split('/')) <= 2:
        click.echo('Please provide a valid path')
        exit(1)

    folder_client = FolderClient(project_code, zone)
    folder_client.create_folder(object_path)
    click.echo(f'Folder created: {object_path}')
    click.echo('Done')
