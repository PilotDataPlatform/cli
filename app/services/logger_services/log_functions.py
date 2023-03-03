# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

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
