# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from multiprocessing import freeze_support

import click
import pkg_resources
from packaging.version import Version

import app.services.output_manager.error_handler as error_handler
import app.services.output_manager.message_handler as mhandler
from app.commands.entry_point import command_groups
from app.commands.entry_point import entry_point
from app.services.output_manager.help_page import get_cli_help_message
from app.utils.aggregated import doc
from app.utils.aggregated import get_latest_cli_version


class ComplexCLI(click.MultiCommand):
    def format_help_text(self, ctx, formatter):
        latest_version = get_latest_cli_version()
        if Version(pkg_resources.get_distribution('app').version) < latest_version:
            self.help += mhandler.SrvOutPutHandler.newer_version_available(latest_version, False)

        click.MultiCommand.format_help_text(self, ctx, formatter)

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
    except Exception as e:
        error_handler.SrvErrorHandler.default_handle(e, True)


if __name__ == '__main__':
    freeze_support()  # Add support for multiprocessing after bundling with PyInstaller
    cli()
