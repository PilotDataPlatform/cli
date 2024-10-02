# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import enum

from app.resources.custom_help import HelpPage

help_msg = HelpPage.page
update = help_msg.get('update', 'default update message')
new_release = ''
for k, v in update.items():
    if k != 'version':
        new_release += f' {k}. {v}\n\n'

update_message = f"\033[92mWhat's new (Version {update.get('version')}):\n\n" + new_release + '\033[0m'


class DatasetHELP(enum.Enum):
    DATASET_DOWNLOAD = 'DATASET_DOWNLOAD'
    DATASET_LIST = 'DATASET_LIST'
    DATASET_SHOW_DETAIL = 'DATASET_SHOW_DETAIL'
    DATASET_VERSION = 'DATASET_VERSION'


def dataset_help_page(DatasetHELP: DatasetHELP):
    helps = help_msg.get('dataset', 'default dataset help')
    return helps.get(DatasetHELP.name)


class ProjectHELP(enum.Enum):
    PROJECT_LIST = 'PROJECT_LIST'


def project_help_page(ProjectHELP: ProjectHELP):
    helps = help_msg.get('project', 'default project help')
    return helps.get(ProjectHELP.name)


class ConfigHELP(enum.Enum):
    SET_CONFIG = 'SET_CONFIG'
    CONFIG_DESTINATION = 'CONFIG_DESTINATION'


def config_help_page(ConfigHELP: ConfigHELP):
    helps = help_msg.get('config', 'default config help')
    return helps.get(ConfigHELP.name)


class UserHELP(enum.Enum):
    USER_LOGIN = 'USER_LOGIN'
    USER_LOGOUT = 'USER_LOGOUT'
    USER_LOGOUT_CONFIRM = 'USER_LOGOUT_CONFIRM'
    USER_LOGIN_USERNAME = 'USER_LOGIN_USERNAME'
    USER_LOGIN_PASSWORD = 'USER_LOGIN_PASSWORD'


def user_help_page(UserHELP: UserHELP):
    helps = help_msg.get('user', 'default user help')
    return helps.get(UserHELP.name)


class FileHELP(enum.Enum):
    FILE_ATTRIBUTE_LIST = 'USER_LOGIN'
    FILE_ATTRIBUTE_EXPORT = 'USER_LOGOUT'
    FILE_LIST = 'USER_LOGOUT_CONFIRM'
    FILE_SYNC = 'USER_LOGIN_USERNAME'
    FILE_UPLOAD = 'USER_LOGIN_PASSWORD'
    FILE_RESUME = 'FILE_RESUME'
    FILE_ATTRIBUTE_P = 'FILE_ATTRIBUTE_P'
    FILE_ATTRIBUTE_N = 'FILE_ATTRIBUTE_N'
    FILE_Z = 'FILE_Z'
    FILE_SYNC_ZIP = 'FILE_SYNC_ZIP'
    FILE_SYNC_I = 'FILE_SYNC_I'
    FILE_SYNC_Z = 'FILE_SYNC_Z'
    FILE_UPLOAD_P = 'FILE_UPLOAD_P'
    FILE_UPLOAD_G = 'FILE_UPLOAD_G'
    FILE_UPLOAD_A = 'FILE_UPLOAD_A'
    FILE_UPLOAD_T = 'FILE_UPLOAD_T'
    FILE_UPLOAD_M = 'FILE_UPLOAD_M'
    FILE_UPLOAD_S = 'FILE_UPLOAD_S'
    FILE_UPLOAD_PIPELINE = 'FILE_UPLOAD_PIPELINE'
    FILE_UPLOAD_ZIP = 'FILE_UPLOAD_ZIP'


def file_help_page(FileHELP: FileHELP):
    helps = help_msg.get('file', 'default file help')
    return helps.get(FileHELP.name)


class ContainerRegistryHELP(enum.Enum):
    LIST_PROJECTS = 'LIST_PROJECTS'
    LIST_REPOSITORIES = 'LIST_REPOSITORIES'
    CREATE_PROJECT = 'CREATE_PROJECT'
    GET_SECRET = 'GET_SECRET'
    SHARE_PROJECT = 'SHARE_PROJECT'


def cr_help_page(ContainerRegistryHELP: ContainerRegistryHELP):
    helps = help_msg.get('container_registry', 'default kg help')
    return helps.get(ContainerRegistryHELP.name)
