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

import app.services.output_manager.help_page as config_help
from app.services.user_authentication.user_set_config import set_config
from app.utils.aggregated import doc


@click.command()
def cli():
    """Config Actions."""
    pass


@click.command()
@click.argument('path', type=click.Path(exists=True), nargs=1)
@click.option(
    '-o',
    '--output',
    type=click.Path(),
    default='.',
    help=config_help.config_help_page(config_help.ConfigHELP.CONFIG_DESTINATION),
)
@doc(config_help.config_help_page(config_help.ConfigHELP.SET_CONFIG))
def set_env(path, output):
    set_config(path, output)
