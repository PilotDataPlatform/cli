import click
from app.services.user_authentication.user_login_logout import user_login, user_logout
import app.services.logger_services.log_functions as logger
import app.services.output_manager.message_handler as mhandler
from app.services.user_authentication.decorator import require_login_session
import app.services.output_manager.help_page as user_help
from app.utils.aggregated import doc

@click.command()
def cli():
    """User Actions"""
    pass

@click.command()
@click.option('-U', '--username', prompt='Username',
              help=(user_help.user_help_page(user_help.UserHELP.USER_LOGIN_USERNAME)))
@click.option('-P', '--password', prompt='Password',
              help=(user_help.user_help_page(user_help.UserHELP.USER_LOGIN_PASSWORD)),
              hide_input=True)
@doc(user_help.user_help_page(user_help.UserHELP.USER_LOGIN))
def login(username, password):
    res = user_login(username, password)
    mhandler.SrvOutPutHandler.login_success()

@click.command()
@click.option('-y', '--yes', is_flag=True,
              callback=mhandler.SrvOutPutHandler.abort_if_false, expose_value=False,
              help=user_help.user_help_page(user_help.UserHELP.USER_LOGOUT_CONFIRM),
              prompt='Are you sure you want to logout?')
@require_login_session
@doc(user_help.user_help_page(user_help.UserHELP.USER_LOGOUT))
def logout():
    user_logout()
    mhandler.SrvOutPutHandler.logout_success()
