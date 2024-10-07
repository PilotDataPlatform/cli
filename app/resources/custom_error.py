# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.


class Error:
    error_msg = {
        'LOGIN_SESSION_INVALID': 'The current login session is invalid. Please login to continue.',
        'PROJECT_DENIED': 'Permission denied. Please verify Project Code and try again.',
        'INVALID_CREDENTIALS': 'Invalid username or password. Please try again.',
        'ERROR_CONNECTION': 'Failed to connect to service. Please check your network and try again.',
        'CODE_NOT_FOUND': 'Project Code not found in your project list. Please verify and try again.',
        'FILE_EXIST': 'File/Folder with the same name already exist in the Project. Please rename and try again.',
        'NO_MANIFEST': 'Attribute Name not found in Project. Please verify and try again.',
        'INVALID_CHOICE_FIELD': (
            "Attribute validation failed. Please verify the attribute value in '%s' is a valid choice and try again."
        ),
        'MANIFEST_NOT_FOUND': 'Attribute validation failed. Please verify Attribute Name and try again.',
        'TEXT_TOO_LONG': (
            "Attribute validation failed. Reduce attribute '%s' length to 100 characters or less and try again."
        ),
        'FIELD_REQUIRED': (
            "Attribute validation failed. Please ensure mandatory attribute '%s' have value and try again."
        ),
        'INVALID_TEMPLATE': 'Attribute validation failed. Please correct JSON format and try again.',
        'LIMIT_TAG_ERROR': 'Tag limit has been reached. A maximum of 10 tags are allowed per file.',
        'INVALID_TAG_ERROR': (
            'Invalid tag format. Tags must be between 1 and 32 characters long '
            'and may only contain lowercase letters, numbers and/or hyphens.'
        ),
        'RESERVED_TAG': 'Invalid tag name. Please rename your tag and try again.',
        'MISSING_REQUIRED_ATTRIBUTE': (
            "Missing required attribute '%s'. Please add missing attribute value and try again."
        ),
        'MANIFEST_NOT_EXIST': "Attribute '%s' not found in Project. Please verify and try again.",
        'INVALID_ATTRIBUTE': "Invalid attribute '%s'. Please verify and try again.",
        'INVALID_UPLOAD_REQUEST': 'Invalid upload request: %s',
        'INVALID_SOURCE_FILE': 'File does not exist or source file provided is invalid: %s',
        'INVALID_LINEAGE': 'Create lineage failed: %s',
        'INVALID_PIPELINENAME': (
            'Invalid pipeline name. Pipeline names must be between 1 and 20 characters long and '
            'may only contain lowercase letters, numbers, and/or special characters of -_, .'
        ),
        'INVALID_PATHS': 'The input path is empty. Please select at least one file or folder to upload',
        'INVALID_RESUMABLE': 'The resumable manifest file is not exist.',
        'INVALID_FOLDERNAME': (
            'The input folder name is not valid. Please follow the rule:\n'
            ' - cannot contains special characters.\n'
            ' - the length should be smaller than 20 characters.'
        ),
        'INVALID_TOKEN': 'Your login session has expired. Please try again or log in again.',
        'PERMISSION_DENIED': (
            'Permission denied. Please verify your role in the Project has permission to perform this action.'
        ),
        'UPLOAD_CANCEL': 'Upload task was cancelled.',
        'UPLOAD_FAIL': 'Upload task was failed. Please check the console output.',
        'UPLOAD_ID_NOT_EXIST': (
            'The specified multipart upload does not exist. '
            'The upload ID may be invalid, or the upload may have been aborted or completed.'
        ),
        'MANIFEST_OF_FOLDER_FILE_EXIST': (
            'The manifest file of folder %s already exist. ' 'Do you want to overwrite the existing manifest file?'
        ),
        'INVALID_CHUNK_UPLOAD': (
            '\nThe chunk number %d is not the same with previous etag.\n'
            'It means the resumable file is not the same with previous one.\n'
            'Please to double check the file content.'
        ),
        'UNSUPPORT_TAG_MANIFEST': 'Tagging and manifest attaching are not supported for folder type.',
        'INVALID_INPUT': 'Invalid input. Please try again.',
        'UNSUPPORTED_PROJECT': 'This function is not supported in the given Project %s',
        'CREATE_FOLDER_IF_NOT_EXIST': 'Target folder does not exist. Would you like to create a new folder?',
        'MISSING_PROJECT_CODE': 'Please provide Project Code and folder directory.',
        'INVALID_PATH': 'Provided file/folder does not exist.',
        'DOWNLOAD_FAIL': 'Download task failed. File cannot be saved to local drive.',
        'FILE_LOCKED': (
            'File/Folder action cannot be proceed at this moment due to other processes. Please try again later.'
        ),
        'NO_FILE_PERMMISION': (
            'File does not exist or you do not have correct permission in Project. '
            'Please verify your role and check that the file exists.'
        ),
        'FOLDER_NOT_FOUND': 'Folder not found in the Project.',
        'INVALID_ZONE': 'The data zone invalid. Please verify the data location and try again.',
        'FOLDER_EMPTY': 'Folder is empty.',
        'RESERVED_FOLDER': 'Reserved folder name, please rename the folder and try again later',
        'INVALID_ACTION': 'Invalid action: %s',
        'DUPLICATE_TAG_ERROR': 'Cannot add duplicate tags',
        'INVALID_FOLDER': 'Provided folder does not exist',
        'INVALID_NAMEFOLDER': 'User name folder is missing or provided user name folder does not exist',
        'INVALID_DOWNLOAD': 'Invalid download, file/folder not exist or folder is empty: %s',
        'VERSION_NOT_EXIST': 'Version not available: %s',
        'DATASET_NOT_EXIST': 'Dataset not found in your dataset list',
        'DATASET_PERMISSION': 'You do not have permission to access this dataset',
        'USER_DISABLED': 'User may not exist or has been disabled',
        'OVER_SIZE': '%s is too large',
        'CONTAINER_REGISTRY_HOST_INVALID': "Invalid host URL. Ensure host begins with 'http://' or 'https://'.",
        'CONTAINER_REGISTRY_401': 'You lack valid authentication credentials for the requested resource.',
        'CONTAINER_REGISTRY_403': 'You do not have permission to access this host or resource.',
        'CONTAINER_REGISTRY_VISIBILITY_INVALID': "Invalid visiblity. Ensure visiblity is 'public' or 'private'.",
        'CONTAINER_REGISTRY_DUPLICATE_PROJECT': 'Project already exists.',
        'CONTAINER_REGISTRY_ROLE_INVALID': (
            "Invalid role. Ensure role is 'admin', 'developer', 'guest', or 'maintainer'."
        ),
        'USER_NOT_FOUND': 'User not found.',
        'CONTAINER_REGISTRY_OTHER': 'Encountered an error when interacting with container registry.',
        'TOU_CONTENT': (
            'You are about to transfer data directly to the PILOT Core! '
            'In accordance with the PILOT Terms of Use, please confirm that you have made your best efforts '
            'to pseudonymize or anonymize the data and that you have the legal authority to transfer and make this '
            'data available for dissemination and use within the PILOT. If you need to process the data to remove '
            'sensitive identifiers, please cancel this transfer and upload the data to the Green Room to perform '
            'these actions.'
        ),
        'CONFIG_NOT_FOUND': 'This cli is not setup properly, please download config file and config again.',
        'CONFIG_EXIST': (
            'This cli has been configured already.'
            'If you want to re-config this cli please remove previous file first'
        ),
        'CONTAINER_REGISTRY_NO_URL': (
            'Container registry has not yet been configured. Related commands cannot be used at this time.'
        ),
    }
