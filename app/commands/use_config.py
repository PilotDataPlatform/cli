# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

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
