# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.


class HelpPage:
    page = {
        'update': {
            'version': '2.2.6',
            '1': 'CLI supports listing of all datasets a project administrator has access to.',
        },
        'dataset': {
            'DATASET_DOWNLOAD': 'Download a dataset or a particular version of a dataset.',
            'DATASET_LIST': 'List accessible datasets.',
            'DATASET_SHOW_DETAIL': 'Show details of a dataset.',
            'DATASET_VERSION': 'Download a particular version of a dataset.',
        },
        'project': {'PROJECT_LIST': 'List accessible projects.'},
        'user': {
            'USER_LOGIN': 'For user to login.',
            'USER_LOGOUT': 'For user to logout.',
            'USER_LOGOUT_CONFIRM': (
                'Input Y/yes to confirm you want to logout, otherwise input N/no to remain logged in.'
            ),
            'USER_LOGIN_USERNAME': 'Specify username for login.',
            'USER_LOGIN_PASSWORD': 'Specify password for login.',
        },
        'file': {
            'FILE_ATTRIBUTE_LIST': 'List attribute templates of a given Project.',
            'FILE_ATTRIBUTE_EXPORT': 'Export attribute template from a given Project.',
            'FILE_LIST': 'List files and folders inside a given Project/folder.',
            'FILE_SYNC': 'Download files/folders from a given Project/folder/file in core zone.',
            'FILE_UPLOAD': 'Upload files/folders to a given Project path.',
            'FILE_RESUME': 'Resume the upload process with given manifest file.',
            'FILE_Z': 'Target Zone (i.e., core/greenroom)  [default: greenroom]',
            'FILE_ATTRIBUTE_P': 'Project Code',
            'FILE_ATTRIBUTE_N': 'Attribute Template Name',
            'FILE_SYNC_ZIP': 'Download files as a zip.',
            'FILE_SYNC_I': 'Enable downloading by geid.',
            'FILE_SYNC_Z': 'Target Zone (i.e., core/greenroom)',
            'FILE_UPLOAD_P': 'Project folder path starting from Project code. (i.e., indoctestproject/user/folder)',
            'FILE_UPLOAD_A': 'File Attribute Template used for annotating files during upload.',
            'FILE_UPLOAD_T': (
                'Add a tag to the file. This option could be used multiple times for adding multiple tags.'
            ),
            'FILE_UPLOAD_M': 'The message used to comment on the purpose of uploading your processed file',
            'FILE_UPLOAD_S': 'The Project path of the source file of your processed files.',
            'FILE_UPLOAD_PIPELINE': (
                "The processed pipeline of your processed files. [only used with '--source' option]"
            ),
            'FILE_UPLOAD_ZIP': 'Upload folder as a compressed zip file.',
        },
        'config': {
            'SET_CONFIG': 'Chose config file and set for cli.',
            'CONFIG_DESTINATION': 'The destination the config file goes to, default will be current cli directory.',
        },
        'container_registry': {
            'LIST_PROJECTS': 'List all projects',
            'LIST_REPOSITORIES': 'List all repositories (optionally: in a given project)',
            'CREATE_PROJECT': 'Create a new project',
            'GET_SECRET': 'Get your user CLI secret',
            'SHARE_PROJECT': 'Share a project with another user',
        },
    }
