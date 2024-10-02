# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

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
