# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


class Error:
    error_msg = {
        "LOGIN_SESSION_INVALID": "The current login session is invalid. Please login to continue.",
        "PROJECT_DENIED": "Permission denied. Please verify Project Code and try again.",
        "INVALID_CREDENTIALS": "Invalid username or password. Please try again.",
        "ERROR_CONNECTION": "Failed to connect to service. Please check your network and try again.",
        "CODE_NOT_FOUND": "Project Code not found in your project list. Please verify and try again.",
        "FILE_EXIST": "File/Folder with the same name already exist in the Project. Please rename and try again.",
        "NO_MANIFEST": "Attribute Name not found in Project. Please verify and try again.",
        "INVALID_CHOICE_FIELD": (
            "Attribute validation failed. Please verify the attribute value in '%s' is a valid choice and try again."),
        "MANIFEST_NOT_FOUND": "Attribute validation failed. Please verify Attribute Name and try again.",
        "TEXT_TOO_LONG": (
            "Attribute validation failed. Reduce attribute '%s' length to 100 characters or less and try again."),
        "FIELD_REQUIRED": (
            "Attribute validation failed. Please ensure mandatory attribute '%s' have value and try again."),
        "INVALID_TEMPLATE": "Attribute validation failed. Please correct JSON format and try again.",
        "LIMIT_TAG_ERROR": "Tag limit has been reached. A maximum of 10 tags are allowed per file.",
        "INVALID_TAG_ERROR": (
            "Invalid tag format. Tags must be between 1 and 32 characters long "
            "and may only contain lowercase letters, numbers and/or hyphens."),
        "RESERVED_TAG": "Invalid tag name. Please rename your tag and try again.",
        "MISSING_REQUIRED_ATTRIBUTE": (
            "Missing required attribute '%s'. Please add missing attribute value and try again."),
        "MANIFEST_NOT_EXIST": "Attribute '%s' not found in Project. Please verify and try again.",
        "INVALID_ATTRIBUTE": "Invalid attribute '%s'. Please verify and try again.",
        "INVALID_UPLOAD_REQUEST": "Invalid upload request: %s",
        "INVALID_SOURCE_FILE": "File does not exist or source file provided is invalid: %s",
        "INVALID_LINEAGE": "Create lineage failed: %s",
        "INVALID_PIPELINENAME": (
            "Invalid pipeline name. Pipeline names must be between 1 and 20 characters long and "
            "may only contain lowercase letters, numbers, and/or special characters of -_, ."),
        "INVALID_TOKEN": "Your login session has expired. Please try again or log in again.",
        "PERMISSION_DENIED": (
            "Permission denied. Please verify your role in the Project has permission to perform this action."),
        "UPLOAD_CANCEL": "Upload task was cancelled.",
        "INVALID_INPUT": "Invalid input. Please try again.",
        "UNSUPPORTED_PROJECT": "This function is not supported in the given Project %s",
        "CREATE_FOLDER_IF_NOT_EXIST": "Target folder does not exist. Would you like to create a new folder?",
        "MISSING_PROJECT_CODE": "Please provide Project Code and folder directory.",
        "INVALID_PATH": "Provided file/folder does not exist.",
        "DOWNLOAD_FAIL": "Download task failed. File cannot be saved to local drive.",
        "FILE_LOCKED": (
            "File/Folder action cannot be proceed at this moment due to other processes. Please try again later."),
        "NO_FILE_PERMMISION": "File does not exist in Project. Please verify your role and check that the file exists.",
        "FOLDER_NOT_FOUND": "Folder not found in the Project.",
        "INVALID_ZONE": "The data zone invalid. Please verify the data location and try again.",
        "FOLDER_EMPTY": "Folder is empty.",
        "RESERVED_FOLDER": "Reserved folder name, please rename the folder and try again later",
        "INVALID_ACTION": "Invalid action: %s",
        "DUPLICATE_TAG_ERROR": "Cannot add duplicate tags",
        "INVALID_FOLDER": "Provided folder does not exist",
        "INVALID_NAMEFOLDER": "User name folder is missing or provided user name folder does not exist",
        "INVALID_DOWNLOAD": "Invalid download, file/folder not exist or folder is empty: %s",
        "VERSION_NOT_EXIST": "Version not available: %s",
        "DATASET_NOT_EXIST": "Dataset not found in your dataset list",
        "DATASET_PERMISSION": "You do not have permission to access this dataset",
        "USER_DISABLED": "User may not exist or has been disabled",
        "CANNOT_AUTH_HPC": "Cannot proceed with HPC authorization request",
        "OVER_SIZE": "%s is too large",
        "CANNOT_PROCESS_HPC_JOB": "Cannot process with HPC: %s",
        "CONTAINER_REGISTRY_HOST_INVALID": "Invalid host URL. Ensure host begins with 'http://' or 'https://'.",
        "CONTAINER_REGISTRY_401": "You lack valid authentication credentials for the requested resource.",
        "CONTAINER_REGISTRY_403": "You do not have permission to access this host or resource.",
        "CONTAINER_REGISTRY_VISIBILITY_INVALID": "Invalid visiblity. Ensure visiblity is 'public' or 'private'.",
        "CONTAINER_REGISTRY_DUPLICATE_PROJECT": "Project already exists.",
        "CONTAINER_REGISTRY_ROLE_INVALID": (
            "Invalid role. Ensure role is 'admin', 'developer', 'guest', or 'maintainer'."),
        "USER_NOT_FOUND": "User not found.",
        "CONTAINER_REGISTRY_OTHER": "Encountered an error when interacting with container registry.",
        "TOU_CONTENT": (
            "You are about to transfer data directly to the PILOT Core! "
            "In accordance with the PILOT Terms of Use, please confirm that you have made your best efforts "
            "to pseudonymize or anonymize the data and that you have the legal authority to transfer and make this "
            "data available for dissemination and use within the PILOT. If you need to process the data to remove "
            "sensitive identifiers, please cancel this transfer and upload the data to the Green Room to perform "
            "these actions."),
        "CONTAINER_REGISTRY_NO_URL": (
            "Container registry has not yet been configured. Related commands cannot be used at this time.")
    }
