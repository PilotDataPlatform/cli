# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import click

import app.services.output_manager.help_page as user_help
import app.services.output_manager.message_handler as mhandler
from app.services.user_authentication.decorator import require_login_session

from app.services.user_authentication.user_login_logout import user_device_id_login
from app.services.user_authentication.user_login_logout import user_logout
from app.services.user_authentication.user_login_logout import validate_user_device_login
from app.utils.aggregated import doc


@click.command()
def cli():
    """User Actions."""
    pass


@click.command()
@doc(user_help.user_help_page(user_help.UserHELP.USER_LOGIN))
def login():
    device_login = user_device_id_login()
    if device_login:
        mhandler.SrvOutPutHandler.login_input_device_code(device_login['verification_uri_complete'])
        mhandler.SrvOutPutHandler.login_device_code_qrcode(device_login['verification_uri_complete'])
    else:
        mhandler.SrvOutPutHandler.login_input_device_error()

    is_validated = validate_user_device_login(
        device_login['device_code'], device_login['expires'], device_login['interval']
    )
    if is_validated:
        mhandler.SrvOutPutHandler.login_success()
    else:
        mhandler.SrvOutPutHandler.validation_login_input_device_error()


@click.command()
@click.option(
    '-y',
    '--yes',
    is_flag=True,
    callback=mhandler.SrvOutPutHandler.abort_if_false,
    expose_value=False,
    help=user_help.user_help_page(user_help.UserHELP.USER_LOGOUT_CONFIRM),
    prompt='Are you sure you want to logout?',
)
@require_login_session
@doc(user_help.user_help_page(user_help.UserHELP.USER_LOGOUT))
def logout():
    user_logout()
    mhandler.SrvOutPutHandler.logout_success()
