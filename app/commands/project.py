import click
from app.services.project_manager.aggregated import SrvProjectManager
import app.services.output_manager.message_handler as mhandler
import app.services.output_manager.help_page as project_help
from app.utils.aggregated import doc

@click.command()
def cli():
    """Project Actions"""
    pass


@click.command(name="list")
@doc(project_help.project_help_page(project_help.ProjectHELP.PROJECT_LIST))
def project_list_all():
    project_mgr = SrvProjectManager()
    project_mgr.list_all()
    mhandler.SrvOutPutHandler.list_success('Project')
