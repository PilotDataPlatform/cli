import click
from app.services.hpc_manager.hpc_auth import HPCTokenManager
from app.services.hpc_manager.hpc_jobs import HPCJobManager
from app.services.hpc_manager.hpc_cluster import HPCNodeManager, HPCPartitionManager
import app.services.output_manager.message_handler as mhandler
import app.services.output_manager.help_page as hpc_help
from app.utils.aggregated import doc
from app.configs.user_config import UserConfig
import app.services.logger_services.log_functions as logger
from app.services.user_authentication.user_login_logout import get_tokens, check_is_login, check_is_active

@click.command()
def cli():
    """HPC Actions"""
    pass


@click.command(name="token")
@click.option('-h', '--host', prompt='Host',
              help=(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_LOGIN_HOST)))
@click.option('-U', '--username', prompt='Username',
              help=(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_LOGIN_USERNAME)))
@click.option('-P', '--password', prompt='Password',
              help=(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_LOGIN_PASSWORD)),
              hide_input=True)
@doc(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_AUTH))
def hpc_auth(host, username, password):
    user = UserConfig()
    is_login = check_is_login(False)
    is_active = check_is_active(False)
    # No login session and no input username, password
    if not (username and password) and not (is_login and is_active):
        username = click.prompt("Username")
        password = click.prompt("Password", hide_input=True)
        token = get_tokens(username, password)[0]
    # Input username and password
    elif username and password:
        if is_login and is_active:
            token = user.access_token
        else:
            token = get_tokens(username, password)[0]
    # No Input username and password, but has login session
    elif not (username and password) and (is_login and is_active):
        username = user.username
        password = user.password
        token = user.access_token
    hpc_mgr = HPCTokenManager(token)
    hpc_token = hpc_mgr.auth_user(host, username, password)
    logger.succeed("Authenticated successfully, token saved")
    user.hpc_token = hpc_token
    user.save()
    


@click.command(name="submit")
@click.option('-h', '--host', prompt='Host',
              help=(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_LOGIN_HOST)))
@click.argument("path",
                type=click.Path(exists=True),
                nargs=1)
@doc(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_SUBMIT))
def hpc_job_submit(host, path):
    hpc_mgr = HPCJobManager()
    submit_job = hpc_mgr.submit_job(host, path)
    for k, v in submit_job.items():
        logger.succeed(f"{k}: {v}")


@click.command(name="get-job")
@click.option('-h', '--host', prompt='Host',
              help=(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_LOGIN_HOST)))
@click.argument("job_id",
                type=click.STRING,
                nargs=1)
@doc(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_JOB_INFO))
def hpc_job_info(host, job_id):
    hpc_mgr = HPCJobManager()
    job_info = hpc_mgr.get_job(host, job_id)
    for k, v in job_info.items():
        if k not in ['standard_input']:
            logger.succeed(f"{k}: {v}")


@click.command(name="list-nodes")
@click.option('-h', '--host', prompt='Host',
              help=(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_LOGIN_HOST)))
@doc(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_NODES))
def hpc_list_nodes(host):
    hpc_mgr = HPCNodeManager()
    nodes = hpc_mgr.list_nodes(host)
    for node in nodes:
        for node_name, node_info in node.items():
            logger.succeed(f"\nNode name: {node_name}")
            row_value = ''
            for k, v in node_info.items():
                row_value = row_value + k + ': ' + str(v) + ' , '
            logger.info(row_value.rstrip(', '))
    logger.succeed('\nAll nodes are listed')

@click.command(name="get-node")
@click.option('-h', '--host', prompt='Host',
              help=(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_LOGIN_HOST)))
@click.argument("node_name",
                type=click.STRING,
                nargs=1)
@doc(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_GET_NODE))
def hpc_get_node(host, node_name):
    hpc_mgr = HPCNodeManager()
    nodes = hpc_mgr.get_node(host, node_name)
    for node in nodes:
        for node_name, node_info in node.items():
            logger.succeed(f"\nNode name: {node_name}")
            row_value = ''
            for k, v in node_info.items():
                row_value = row_value + k + ': ' + str(v) + ' , '
            logger.info(row_value.rstrip(', '))
    logger.succeed('\n')


@click.command(name="list-partitions")
@click.option('-h', '--host', prompt='Host',
              help=(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_LOGIN_HOST)))
@doc(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_PARTITIONS))
def hpc_list_partitions(host):
    hpc_mgr = HPCPartitionManager()
    partitions = hpc_mgr.list_partitions(host)
    for partition in partitions:
        for partition_name, partition_info in partition.items():
            logger.succeed(f"\nPartition name: {partition_name}")
            row_value = ''
            for k, v in partition_info.items():
                if k == 'tres':
                    value = str(v).replace(',', ', ')
                else:
                    value = ', '.join(v)
                row_value = row_value + k + ': ' + value + ' \n'
            logger.info(row_value.rstrip(', '))
    logger.succeed('\nAll partitions are listed')

@click.command(name="get-partition")
@click.option('-h', '--host', prompt='Host',
              help=(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_LOGIN_HOST)))
@click.argument("partition_name",
                type=click.STRING,
                nargs=1)
@doc(hpc_help.hpc_help_page(hpc_help.HpcHELP.HPC_GET_PARTITION))
def hpc_get_partition(host, partition_name):
    hpc_mgr = HPCPartitionManager()
    partitions = hpc_mgr.get_partition(host, partition_name)
    for partition in partitions:
        for partition_name, partition_info in partition.items():
            logger.succeed(f"\nPartition name: {partition_name}")
            row_value = ''
            for k, v in partition_info.items():
                if k == 'tres':
                    value = str(v).replace(',', ', ')
                else:
                    value = ', '.join(v)
                row_value = row_value + k + ': ' + value + ' \n'
            logger.info(row_value)
