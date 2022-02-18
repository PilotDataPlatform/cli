from app.configs.app_config import AppConfig
from app.resources.custom_help import HelpPage
import enum

help_msg = HelpPage.page
update = help_msg.get('update', 'default update message')
new_release = ''
for k, v in update.items():
    if k != 'version':
        new_release += f' {k}. {v}\n\n'

update_message = f"\033[92mWhat's new (Version {update.get('version')}):\n\n" + new_release + '\033[0m'


class DatasetHELP(enum.Enum):
    DATASET_DOWNLOAD = "DATASET_DOWNLOAD"
    DATASET_LIST = "DATASET_LIST"
    DATASET_SHOW_DETAIL = "DATASET_SHOW_DETAIL"
    DATASET_VERSION = "DATASET_VERSION"


def dataset_help_page(DatasetHELP: DatasetHELP):
    help = help_msg.get('dataset', 'default dataset help')
    return help.get(DatasetHELP.name)

class ProjectHELP(enum.Enum):
    PROJECT_LIST = "PROJECT_LIST"


def project_help_page(ProjectHELP: ProjectHELP):
    help = help_msg.get('project', 'default project help')
    return help.get(ProjectHELP.name)

class UserHELP(enum.Enum):
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_LOGOUT_CONFIRM = "USER_LOGOUT_CONFIRM"
    USER_LOGIN_USERNAME = "USER_LOGIN_USERNAME"
    USER_LOGIN_PASSWORD = "USER_LOGIN_PASSWORD"


def user_help_page(UserHELP: UserHELP):
    help = help_msg.get('user', 'default user help')
    return help.get(UserHELP.name)


class FileHELP(enum.Enum):
    FILE_ATTRIBUTE_LIST = "USER_LOGIN"
    FILE_ATTRIBUTE_EXPORT = "USER_LOGOUT"
    FILE_LIST = "USER_LOGOUT_CONFIRM"
    FILE_SYNC = "USER_LOGIN_USERNAME"
    FILE_UPLOAD = "USER_LOGIN_PASSWORD"
    FILE_ATTRIBUTE_P = "FILE_ATTRIBUTE_P"
    FILE_ATTRIBUTE_N = "FILE_ATTRIBUTE_N"
    FILE_Z = "FILE_Z"
    FILE_SYNC_ZIP = "FILE_SYNC_ZIP"
    FILE_SYNC_I = "FILE_SYNC_I"
    FILE_SYNC_Z = "FILE_SYNC_Z"
    FILE_UPLOAD_P = "FILE_UPLOAD_P"
    FILE_UPLOAD_G = "FILE_UPLOAD_G"
    FILE_UPLOAD_A = "FILE_UPLOAD_A"
    FILE_UPLOAD_T = "FILE_UPLOAD_T"
    FILE_UPLOAD_M = "FILE_UPLOAD_M"
    FILE_UPLOAD_S = "FILE_UPLOAD_S"
    FILE_UPLOAD_PIPELINE = "FILE_UPLOAD_PIPELINE"
    FILE_UPLOAD_ZIP = "FILE_UPLOAD_ZIP"

def file_help_page(FileHELP: FileHELP):
    help = help_msg.get('file', 'default file help')
    return help.get(FileHELP.name)


class HpcHELP(enum.Enum):
    HPC_AUTH = "HPC_AUTH"
    HPC_LOGIN_HOST = "HPC_LOGIN_HOST"
    HPC_LOGIN_USERNAME = "HPC_LOGIN_USERNAME"
    HPC_LOGIN_PASSWORD = "HPC_LOGIN_PASSWORD"
    HPC_TOKEN = "HPC_TOKEN"
    HPC_SUBMIT = "HPC_SUBMIT"
    HPC_JOB_INFO = "HPC_JOB_INFO"
    HPC_NODES = "HPC_NODES"
    HPC_GET_NODE = "HPC_GET_NODE"
    HPC_PARTITIONS = "HPC_PARTITIONS"
    HPC_GET_PARTITION = "HPC_GET_PARTITION"


def hpc_help_page(HpcHELP: HpcHELP):
    help = help_msg.get('hpc', 'default hpc help')
    return help.get(HpcHELP.name)

class KgResourceHELP(enum.Enum):
    KG_IMPORT = "KG_IMPORT"
    KG_DATASET_CODE = "KG_DATASET_CODE"


def kg_resource_help_page(KgResourceHELP: KgResourceHELP):
    help = help_msg.get('knowledge_graph', 'default kg help')
    return help.get(KgResourceHELP.name)

class ContainerRegistryHELP(enum.Enum):
    LIST_PROJECTS = "LIST_PROJECTS"
    LIST_REPOSITORIES = "LIST_REPOSITORIES"
    CREATE_PROJECT = "CREATE_PROJECT"
    GET_SECRET = "GET_SECRET"
    SHARE_PROJECT = "SHARE_PROJECT"

def cr_help_page(ContainerRegistryHELP: ContainerRegistryHELP):
    help = help_msg.get('container_registry', 'default kg help')
    return help.get(ContainerRegistryHELP.name)
