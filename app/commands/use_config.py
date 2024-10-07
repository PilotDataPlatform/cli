# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

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
