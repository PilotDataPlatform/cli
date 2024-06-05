# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from multiprocessing import freeze_support

import click
import requests

import app.services.output_manager.error_handler as error_handler
from app.commands.entry_point import command_groups
from app.commands.entry_point import entry_point
from app.services.output_manager.help_page import get_cli_help_message
from app.utils.aggregated import doc


class ComplexCLI(click.MultiCommand):
    def list_commands(self, ctx):
        rv = command_groups()
        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            mod = __import__(f'app.commands.{name}', None, None, ['cli'])
        except ImportError:
            return
        return mod.cli


@click.command(cls=ComplexCLI)
@doc(get_cli_help_message())
def cli():
    try:
        entry_point()
    except requests.exceptions.ConnectionError:
        error_handler.SrvErrorHandler.customized_handle(error_handler.ECustomizedError.ERROR_CONNECTION, True)
    except Exception as e:
        error_handler.SrvErrorHandler.default_handle(e, True)


if __name__ == '__main__':
    freeze_support()  # Add support for multiprocessing after bundling with PyInstaller
    cli()
