# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import sys
from typing import Union

import click
import pkg_resources
from packaging.version import Version

import app.services.output_manager.help_page as user_help
import app.services.output_manager.message_handler as mhandler
from app.models.enums import LoginMethod
from app.services.user_authentication.decorator import require_login_session
from app.services.user_authentication.user_login_logout import login_using_api_key
from app.services.user_authentication.user_login_logout import user_device_id_login
from app.services.user_authentication.user_login_logout import user_logout
from app.services.user_authentication.user_login_logout import validate_user_device_login
from app.utils.aggregated import doc
from app.utils.aggregated import get_latest_cli_version


@click.command()
def cli():
    """User Actions."""
    pass


@click.command()
@click.option(
    '--api-key',
    envvar='PILOT_API_KEY',
    help=(user_help.user_help_page(user_help.UserHELP.USER_LOGIN_API_KEY)),
)
@doc(user_help.user_help_page(user_help.UserHELP.USER_LOGIN))
def login(api_key: Union[str, None]):
    if api_key:
        mhandler.SrvOutPutHandler.login_using_method(LoginMethod.API_KEY)
        is_valid = login_using_api_key(api_key)
        if is_valid:
            mhandler.SrvOutPutHandler.login_success()
        else:
            mhandler.SrvOutPutHandler.login_using_api_key_failed_error()
            sys.exit(1)
    else:
        mhandler.SrvOutPutHandler.login_using_method(LoginMethod.DEVICE_CODE)
        device_login = user_device_id_login()
        if device_login:
            mhandler.SrvOutPutHandler.login_input_device_code(device_login['verification_uri_complete'])
            mhandler.SrvOutPutHandler.login_device_code_qrcode(device_login['verification_uri_complete'])
        else:
            mhandler.SrvOutPutHandler.login_input_device_error()
            sys.exit(1)

        is_validated = validate_user_device_login(
            device_login['device_code'], device_login['expires'], device_login['interval']
        )
        if is_validated:
            mhandler.SrvOutPutHandler.login_success()
        else:
            mhandler.SrvOutPutHandler.validation_login_input_device_error()
            sys.exit(1)

    # message user if there is a newer version of the CLI
    latest_version = get_latest_cli_version()
    if Version(pkg_resources.get_distribution('app').version) < latest_version:
        mhandler.SrvOutPutHandler.newer_version_available(latest_version)


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
