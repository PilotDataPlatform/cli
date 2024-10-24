# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.


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
        'INVALID_TAG_FILE': 'Tag files validation failed. Please correct JSON format and try again.',
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
        'INVALID_PIPELINENAME': (
            'Invalid pipeline name. Pipeline names must be between 1 and 20 characters long and '
            'may only contain lowercase letters, numbers, and/or special characters of -_, .'
        ),
        'INVALID_PATHS': 'The input path is empty. Please select at least one file or folder to upload',
        'INVALID_RESUMABLE': 'The resumable manifest file is not exist.',
        'INVALID_FOLDERNAME': (
            'The input folder name is not valid. Please follow the rule:\n'
            ' - cannot contains special characters.\n'
            ' - the length should be smaller than or equal to 100 characters.'
        ),
        'INVALID_TOKEN': 'Your login session has expired. Please try again or log in again.',
        'PERMISSION_DENIED': (
            'Permission denied. Please verify your role in the Project has permission to perform this action.'
        ),
        'UPLOAD_CANCEL': 'Upload task was cancelled.',
        'UPLOAD_FAIL': 'Upload task was failed. Please check the console output.',
        'UPLOAD_SKIP_DUPLICATION': (
            '\nSome of the selected files cannot be uploaded.\n\n'
            'The following files already exist in the upload destination: \n%s\n'
            'Do you want to cancel the upload [N] or skip duplicates and continue uploading [y]?'
        ),
        'UPLOAD_ID_NOT_EXIST': (
            'The specified multipart upload does not exist. '
            'The upload ID may be invalid, or the upload may have been aborted or completed.'
        ),
        'MANIFEST_OF_FOLDER_FILE_EXIST': (
            'The manifest file of folder %s already exist. ' 'To continue and overwrite the resumable upload log, enter'
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
        'DOWNLOAD_SIZE_MISMATCH': 'Download task failed. File size mismatch: original size %s, downloaded size %s',
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
        'INVALID_PROJECT_PATH': 'root folder is missing or provided name/shared folder does not exist',
        'INVALID_DOWNLOAD': 'Invalid download, file/folder not exist or folder is empty: %s',
        # delete command related error
        'INVALID_DELETE_PATH': 'Selected path: %s is invalid.',
        'DELETE_PATH_NOT_EXIST': 'Selected path: %s does not exist.',
        'TRASH_FAIL': 'Failed to trash items: %s.',
        'DELETE_FAIL': 'Failed to delete items: %s.',
        'ALREADY_TRASHED': 'Selected path: %s is already in the trash. Please use permanent delete to remove it.',
        # file metadata related error
        'LOCAL_METADATA_FILE_EXISTS': 'Following metadata file already exists in the local directory: ',
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
            'You are about to transfer data directly to the Pilot Core. '
            'In accordance with the Pilot Terms of Use, please confirm that you have made your best efforts '
            'to pseudonymize or anonymize the data and that you have the legal authority to transfer and make this '
            'data available for dissemination and use within Pilot. If you need to process the data to remove '
            'sensitive identifiers, please cancel this transfer and upload the data to the Green Room to perform '
            'these actions.'
        ),
        'CONFIG_INVALID_PERMISSIONS': 'Cannot proceed with current config permissions.\n%s',
        'CONTAINER_REGISTRY_NO_URL': (
            'Container registry has not yet been configured. Related commands cannot be used at this time.'
        ),
        # folder related error
        'INVALID_FOLDER_PATH': 'Invalid folder path: cannot create name folder or shared folder in cli',
    }
