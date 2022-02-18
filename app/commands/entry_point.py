import click
from .user import login, logout
from .project import project_list_all
from .file import file_put, file_check_manifest, file_export_manifest, file_list, file_download
from .dataset import dataset_list, dataset_show_detail, dataset_download
from .hpc import hpc_auth, hpc_job_info, hpc_job_submit
from .hpc import hpc_list_nodes, hpc_get_node, hpc_list_partitions, hpc_get_partition
from .kg_resource import kg_resource
from .container_registry import create_project, list_projects, list_repositories, get_secret, invite_member
from app.services.user_authentication.decorator import require_login_session

def command_groups():
    commands = ['file', 'user', 'project', 'dataset', 'hpc', 'kg_resource', 'container_registry']
    return commands

@click.group()
def entry_point():
    pass

@entry_point.group(name="project")
@require_login_session
def project_group():
    pass

@entry_point.group(name="dataset")
@require_login_session
def dataset_group():
    pass

@entry_point.group(name="file")
@require_login_session
def file_group():
    pass

@entry_point.group(name="user")
def user_group():
    pass

@entry_point.group(name="hpc")
def hpc_group():
    pass

@entry_point.group(name="kg_resource")
def kg_resource_group():
    pass

@entry_point.group(name="container_registry")
def cr_group():
    pass

file_group.add_command(file_put)
file_group.add_command(file_check_manifest)
file_group.add_command(file_export_manifest)
file_group.add_command(file_list)
file_group.add_command(file_download)
project_group.add_command(project_list_all)
user_group.add_command(login)
user_group.add_command(logout)
dataset_group.add_command(dataset_list)
dataset_group.add_command(dataset_show_detail)
dataset_group.add_command(dataset_download)
hpc_group.add_command(hpc_auth)
hpc_group.add_command(hpc_job_submit)
hpc_group.add_command(hpc_job_info)
hpc_group.add_command(hpc_list_nodes)
hpc_group.add_command(hpc_get_node)
hpc_group.add_command(hpc_list_partitions)
hpc_group.add_command(hpc_get_partition)
kg_resource_group.add_command(kg_resource)
cr_group.add_command(list_projects)
cr_group.add_command(list_repositories)
cr_group.add_command(create_project)
cr_group.add_command(get_secret)
cr_group.add_command(invite_member)
