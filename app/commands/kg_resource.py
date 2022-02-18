from sys import path
import click
from app.services.dataset_manager.dataset_detail import SrvDatasetDetailManager
import app.services.output_manager.message_handler as mhandler
import app.services.output_manager.help_page as kg_help
from app.services.kg_manager.kg_resource import SrvKGResourceMgr
from app.utils.aggregated import doc
from app.configs.user_config import UserConfig
import app.services.logger_services.log_functions as logger
from app.services.user_authentication.user_login_logout import user_login, check_is_login, check_is_active

@click.command()
def cli():
    """KnowledgeGraph Actions"""
    pass


@click.command(name="import")
@click.argument("paths",
                type=click.Path(exists=True),
                nargs=-1)
# @click.option('-c', '--code', help=kg_help.kg_resource_help_page(kg_help.KgResourceHELP.KG_DATASET_CODE))
@doc(kg_help.kg_resource_help_page(kg_help.KgResourceHELP.KG_IMPORT))
def kg_resource(paths):
    kg = SrvKGResourceMgr(paths)
    kg.import_resource()
