# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import enum
import sys

import app.services.logger_services.log_functions as logger
from app.models.service_meta_class import MetaService
from app.resources.custom_error import Error


class ECustomizedError(enum.Enum):
    LOGIN_SESSION_INVALID = ('LOGIN_SESSION_INVALID',)
    PROJECT_DENIED = ('PROJECT_DENIED',)
    INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'
    ERROR_CONNECTION = 'ERROR_CONNECTION'
    CODE_NOT_FOUND = 'CODE_NOT_FOUND'
    FILE_EXIST = 'FILE_EXIST'
    MANIFEST_NOT_EXIST = 'MANIFEST_NOT_EXIST'
    INVALID_CHOICE_FIELD = 'INVALID_CHOICE_FIELD'
    TEXT_TOO_LONG = 'TEXT_TOO_LONG'
    FIELD_REQUIRED = 'FIELD_REQUIRED'
    INVALID_TEMPLATE = 'INVALID_TEMPLATE'
    LIMIT_TAG_ERROR = 'LIMIT_TAG_ERROR'
    INVALID_TAG_ERROR = 'INVALID_TAG_ERROR'
    RESERVED_TAG = 'RESERVED_TAG'
    INVALID_ATTRIBUTE = 'INVALID_ATTRIBUTE'
    MISSING_REQUIRED_ATTRIBUTE = 'MISSING_REQUIRED_ATTRIBUTE'
    INVALID_UPLOAD_REQUEST = 'INVALID_UPLOAD_REQUEST'
    INVALID_SOURCE_FILE = 'INVALID_SOURCE_FILE'
    INVALID_LINEAGE = 'INVALID_LINEAGE'
    INVALID_PIPELINENAME = 'INVALID_PIPELINENAME'
    INVALID_PATHS = 'INVALID_PATHS'
    INVALID_RESUMABLE = 'INVALID_RESUMABLE'
    TOU_CONTENT = 'TOU_CONTENT'
    INVALID_TOKEN = 'INVALID_TOKEN'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    UPLOAD_CANCEL = 'UPLOAD_CANCEL'
    UPLOAD_FAIL = 'UPLOAD_FAIL'
    # the error when multipart upload id is not exist
    UPLOAD_ID_NOT_EXIST = 'UPLOAD_ID_NOT_EXIST'
    MANIFEST_OF_FOLDER_FILE_EXIST = 'MANIFEST_OF_FOLDER_FILE_EXIST'
    # the error when chunk md5 is not match
    INVALID_CHUNK_UPLOAD = 'INVALID_CHUNK_UPLOAD'
    UNSUPPORT_TAG_MANIFEST = 'UNSUPPORT_TAG_MANIFEST'
    MANIFEST_NOT_FOUND = 'MANIFEST_NOT_FOUND'
    INVALID_INPUT = 'INVALID_INPUT'
    UNSUPPORTED_PROJECT = 'UNSUPPORTED_PROJECT'
    CREATE_FOLDER_IF_NOT_EXIST = 'CREATE_FOLDER_IF_NOT_EXIST'
    MISSING_PROJECT_CODE = 'MISSING_PROJECT_CODE'
    INVALID_PATH = 'INVALID_PATH'
    DOWNLOAD_FAIL = 'DOWNLOAD_FAIL'
    FILE_LOCKED = 'FILE_LOCKED'
    NO_FILE_PERMMISION = 'NO_FILE_PERMMISION'
    FOLDER_NOT_FOUND = 'FOLDRER_NOT_FOUND'
    INVALID_ZONE = 'INVALID_ZONE'
    FOLDER_EMPTY = 'FOLDER_EMPTY'
    INVALID_FOLDERNAME = 'INVALID_FOLDERNAME'
    RESERVED_FOLDER = 'RESERVED_FOLDER'
    INVALID_ACTION = 'INVALID_ACTION'
    INVALID_FOLDER = 'INVALID_FOLDER'
    INVALID_NAMEFOLDER = 'INVALID_NAMEFOLDER'
    INVALID_DOWNLOAD = 'INVALID_DOWNLOAD'
    DUPLICATE_TAG_ERROR = 'DUPLICATE_TAG_ERROR'
    VERSION_NOT_EXIST = 'VERSION_NOT_EXIST'
    DATASET_NOT_EXIST = 'DATASET_NOT_EXIST'
    DATASET_PERMISSION = 'DATASET_PERMISSION'
    USER_DISABLED = 'USER_DISABLED'
    OVER_SIZE = 'OVER_SIZE'
    CONTAINER_REGISTRY_HOST_INVALID = 'CONTAINER_REGISTRY_HOST_INVALID'
    CONTAINER_REGISTRY_401 = 'CONTAINER_REGISTRY_401'
    CONTAINER_REGISTRY_403 = 'CONTAINER_REGISTRY_403'
    CONTAINER_REGISTRY_VISIBILITY_INVALID = 'CONTAINER_REGISTRY_VISIBILITY_INVALID'
    CONTAINER_REGISTRY_DUPLICATE_PROJECT = 'CONTAINER_REGISTRY_DUPLICATE_PROJECT'
    CONTAINER_REGISTRY_ROLE_INVALID = 'CONTAINER_REGISTRY_ROLE_INVALID'
    USER_NOT_FOUND = 'USER_NOT_FOUND'
    CONTAINER_REGISTRY_OTHER = 'CONTAINER_REGISTRY_OTHER'
    CONTAINER_REGISTRY_NO_URL = 'CONTAINER_REGISTRY_NO_URL'
    CONFIG_NOT_FOUND = 'CONFIG_NOT_FOUND'
    CONFIG_EXIST = 'CONFIG_EXIST'


def customized_error_msg(customized_error: ECustomizedError):
    if customized_error.name == 'TOU_CONTENT':
        tou_msg = Error.error_msg.get(customized_error.name, 'Unknown error.')
        error_msg = f'\033[92m{tou_msg}\033[0m \n '
        msg = (
            error_msg
            + 'To cancel this transfer, enter [n/No] \n To confirm and proceed with the data transfer, enter [y/Yes] \n'
        )
    else:
        msg = Error.error_msg.get(customized_error.name, 'Unknown error.')
    return msg


class SrvErrorHandler(metaclass=MetaService):
    @staticmethod
    def default_handle(err, if_exit=False):
        logger.error(str(err))
        if if_exit:
            sys.exit(0)

    @staticmethod
    def customized_handle(customized_error: ECustomizedError, if_exit=False, value=None):
        if value:
            logger.error(customized_error_msg(customized_error) % value)  # noqa: G002
        else:
            logger.error(customized_error_msg(customized_error))
        if if_exit:
            sys.exit(0)


class OverSizeError(Exception):
    def __init__(self, message='File size is too large'):
        super().__init__(message)
