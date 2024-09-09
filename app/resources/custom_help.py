# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pkg_resources


class HelpPage:
    page = {
        'update': {
            'version': pkg_resources.get_distribution('app').version,
            '1': 'Add integrity check when downloading.',
            '2': 'Add notification for new version.',
            '3': 'Support Windows platform.',
        },
        'dataset': {
            'DATASET_DOWNLOAD': 'Download a dataset or a particular version of a dataset.',
            'DATASET_LIST': 'List datasets belonging to logged in user.',
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
            'USER_LOGIN_API_KEY': 'Specify API Key for login.',
        },
        'file': {
            'FILE_ATTRIBUTE_LIST': 'List attribute templates of a given Project.',
            'FILE_ATTRIBUTE_EXPORT': 'Export attribute template from a given Project.',
            'FILE_LIST': 'List files and folders inside a given Project/folder.',
            'FILE_SYNC': 'Download files/folders from a given Project/folder/file in core zone.',
            'FILE_UPLOAD': 'Upload files/folders to a given Project path (eg. <project>/users/<user>/<path>).',
            'FILE_RESUME': 'Resume the upload process with a resumable upload log.',
            'FILE_Z': 'Target Zone (i.e., core/greenroom).',
            'FILE_ATTRIBUTE_P': 'Project Code',
            'FILE_ATTRIBUTE_N': 'Attribute Template Name',
            'FILE_SYNC_ZIP': 'Download files as a zip.',
            'FILE_SYNC_I': 'Enable downloading by geid.',
            'FILE_SYNC_Z': 'Target Zone (i.e., core/greenroom).',
            'FILE_UPLOAD_A': 'Add attributes to the file using a File Attribute Template.',
            'FILE_UPLOAD_T': 'Add tags to the file using a Tag file.',
            'FILE_UPLOAD_M': 'The message used to comment on the purpose of uploading your processed file.',
            'FILE_UPLOAD_S': (
                'Project file path for identifying a source file when creating an upstream '
                'file lineage node. Source files must exist in the Core zone.'
            ),
            'FILE_UPLOAD_PIPELINE': (
                "The processed pipeline of your processed files. [only used with '--source' option]"
            ),
            'FILE_UPLOAD_ZIP': 'Upload folder as a compressed zip file.',
            'FILE_META': 'Download metadata file of a given file in target zone.',
            'FILE_META_Z': 'Target Zone (i.e., core/greenroom).',
            'FILE_META_G': 'The location of general metadata file',
            'FILE_META_A': 'The location of attribute metadata file',
            'FILE_META_T': 'The location of tag metadata file',
            'FILE_MOVE': 'Move/Rename files/folders to a given Project path.',
            'FILE_MOVE_Z': 'Target Zone (i.e., core/greenroom).',
            'FILE_MOVE_Y': 'Skip the prompt confirmation and create non-existing folders.',
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
        'folder': {
            'FOLDER_CREATE': 'Create folders/subfolders in project.',
        },
    }
