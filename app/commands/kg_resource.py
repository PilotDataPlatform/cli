# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import click

import app.services.output_manager.help_page as kg_help
from app.services.kg_manager.kg_resource import SrvKGResourceMgr
from app.utils.aggregated import doc


@click.command()
def cli():
    """KnowledgeGraph Actions."""
    pass


@click.command(name='import')
@click.argument('paths', type=click.Path(exists=True), nargs=-1)
@doc(kg_help.kg_resource_help_page(kg_help.KgResourceHELP.KG_IMPORT))
def kg_resource(paths):
    kg = SrvKGResourceMgr(paths)
    kg.import_resource()
