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

import app.services.output_manager.help_page as user_help
import app.services.output_manager.message_handler as mhandler
from app.services.user_authentication.decorator import require_login_session
from app.services.user_authentication.user_login_logout import user_login
from app.services.user_authentication.user_login_logout import user_logout
from app.utils.aggregated import doc


@click.command()
def cli():
    """User Actions."""
    pass


@click.command()
@click.option(
    '-U', '--username', prompt='Username', help=(user_help.user_help_page(user_help.UserHELP.USER_LOGIN_USERNAME))
)
@click.option(
    '-P',
    '--password',
    prompt='Password',
    help=(user_help.user_help_page(user_help.UserHELP.USER_LOGIN_PASSWORD)),
    hide_input=True,
)
@doc(user_help.user_help_page(user_help.UserHELP.USER_LOGIN))
def login(username, password):
    user_login(username, password)
    mhandler.SrvOutPutHandler.login_success()


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
