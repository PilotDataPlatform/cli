# Copyright (C) 2022-2025 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from multiprocessing import freeze_support

import click
import pkg_resources
from click.formatting import HelpFormatter
from packaging.version import Version

import app.services.output_manager.error_handler as error_handler
import app.services.output_manager.message_handler as mhandler
from app.commands.entry_point import command_groups
from app.commands.entry_point import entry_point
from app.services.output_manager.help_page import get_cli_help_message
from app.utils.aggregated import doc
from app.utils.aggregated import get_latest_cli_version


class CustomHelpFormatter(HelpFormatter):
    def __init__(self, *args, **kwargs):
        # Set a desired width to avoid wrapping of the help text
        kwargs['width'] = 200
        super().__init__(*args, **kwargs)

    def write_dl(self, rows, col_max=80, col_spacing=2):
        if rows:
            # get max width of command
            widths = max([len(row[0]) for row in rows])
            for command, help_doc in rows:
                self.write(f'{command:<{widths}}  ')
                if help_doc:
                    while len(help_doc) > col_max:
                        # find the last space within the col_max
                        last_space = help_doc[:col_max].rfind(' ')
                        if last_space == -1:
                            last_space = col_max
                        last_space += 1

                        self.write(f'{help_doc[:last_space]}\n')
                        # filling the new line with indent spacing
                        self.write(' ' * (widths + col_spacing))
                        help_doc = help_doc[last_space:]

                    self.write(f'{help_doc}')
                    self.write('\n')


click.Context.formatter_class = CustomHelpFormatter


class ComplexCLI(click.MultiCommand):
    def format_help_text(self, ctx, formatter):
        latest_version, download_url = get_latest_cli_version()
        if Version(pkg_resources.get_distribution('app').version) < latest_version:
            mhandler.SrvOutPutHandler.newer_version_available(latest_version, download_url)

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
