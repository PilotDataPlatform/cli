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


def warning(*msgs):
    message = ' '.join([str(msg) for msg in msgs])
    click.secho(str(message), fg='yellow')


def error(*msgs):
    message = ' '.join([str(msg) for msg in msgs])
    click.secho(str(message), fg='red')


def succeed(*msgs):
    message = ' '.join([str(msg) for msg in msgs])
    click.secho(str(message), fg='green')


def info(*msgs):
    message = ' '.join([str(msg) for msg in msgs])
    click.secho(str(message), fg='white')
