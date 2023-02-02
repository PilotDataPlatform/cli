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
import requests

import app.services.output_manager.error_handler as error_handler
from app.commands.entry_point import command_groups
from app.commands.entry_point import entry_point
from app.services.output_manager.help_page import update_message
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
@doc(update_message)
def cli():
    try:
        entry_point()
    except requests.exceptions.ConnectionError:
        error_handler.SrvErrorHandler.customized_handle(error_handler.ECustomizedError.ERROR_CONNECTION, True)
    except Exception as e:
        error_handler.SrvErrorHandler.default_handle(e, True)


if __name__ == '__main__':
    cli()
