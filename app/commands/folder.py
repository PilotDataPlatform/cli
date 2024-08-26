# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import click

import app.services.output_manager.message_handler as message_handler
from app.configs.app_config import AppConfig
from app.services.file_manager.file_metadata.folder_client import FolderClient
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.output_manager.help_page import FileHELP
from app.services.output_manager.help_page import FolderHelp
from app.services.output_manager.help_page import file_help_page
from app.services.output_manager.help_page import folder_help_page
from app.utils.aggregated import doc
from app.utils.aggregated import validate_folder_name


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

    # user cannot create root/name/shared folder in cli
    # and folder name must NOT contain special characters[/:?.\\*<>|”\']
    path_list = object_path.split('/')
    if len(path_list) <= 2:
        SrvErrorHandler.customized_handle(ECustomizedError.INVALID_FOLDER_PATH, True)
    for p in path_list:
        if not validate_folder_name(p):
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_FOLDERNAME, True)

    folder_client = FolderClient(project_code, zone)
    folder_client.create_folder(object_path)
    message_handler.SrvOutPutHandler.folder_create(project_code, object_path)
