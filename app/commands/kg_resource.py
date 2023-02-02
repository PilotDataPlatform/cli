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
