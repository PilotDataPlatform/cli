import os.path
from sys import version_info
import click
from app.services.file_manager.file_upload import simple_upload, assemble_path
import app.services.logger_services.log_functions as logger
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler, customized_error_msg
from app.configs.user_config import UserConfig
from app.configs.app_config import AppConfig
from app.services.user_authentication.decorator import require_valid_token
from app.services.dataset_manager.dataset_list import SrvDatasetListManager
from app.services.dataset_manager.dataset_detail import SrvDatasetDetailManager
from app.services.dataset_manager.dataset_download import SrvDatasetDownloadManager
import app.services.output_manager.message_handler as message_handler
import app.services.output_manager.help_page as dataset_help
from app.utils.aggregated import *


@click.command()
def cli():
    """Dataset Actions"""
    pass


@click.command(name="list")
@doc(dataset_help.dataset_help_page(dataset_help.DatasetHELP.DATASET_LIST))
def dataset_list():
    list_mgr = SrvDatasetListManager()
    list_mgr.list_datasets()
    message_handler.SrvOutPutHandler.list_success('Dataset')


@click.command(name="show-detail")
@click.argument("code",
                type=click.STRING,
                nargs=1)
@doc(dataset_help.dataset_help_page(dataset_help.DatasetHELP.DATASET_SHOW_DETAIL))
def dataset_show_detail(code):
    detail_mgr = SrvDatasetDetailManager()
    detail_mgr.dataset_detail(code)


@click.command(name="download")
@click.argument("code",
                type=click.STRING,
                nargs=-1)
@click.argument("output_path",
                type=click.Path(exists=True),
                nargs=1)
@click.option('-v', '--version',
              default=None,
              required=False,
              help=dataset_help.dataset_help_page(dataset_help.DatasetHELP.DATASET_VERSION),
              show_default=True)
@doc(dataset_help.dataset_help_page(dataset_help.DatasetHELP.DATASET_DOWNLOAD))
def dataset_download(code, output_path, version): 
    srv_detail = SrvDatasetDetailManager(interactive=False)
    for dataset_code in code:
        dataset_info = srv_detail.dataset_detail(dataset_code)
        if not dataset_info:
            continue
        dataset_geid = dataset_info.get('general_info').get('global_entity_id')
        available_versions = [v.get('version') for v in dataset_info.get('version_detail')]
        srv_download = SrvDatasetDownloadManager(output_path, dataset_code, dataset_geid)
        if not version:
            srv_download.download_dataset()
        elif version and (version not in available_versions):
            SrvErrorHandler.customized_handle(ECustomizedError.VERSION_NOT_EXIST, False, version)
        else:
            message_handler.SrvOutPutHandler.dataset_current_version(version)
            srv_download.download_dataset_version(version)
        




