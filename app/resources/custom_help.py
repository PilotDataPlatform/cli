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


class HelpPage:
    page = {
        "update": {
            "version": "1.8.0",
            "1": "Harbor container authentication",
            "2": "Harbor create project and list project",
            "3": "Harbor list repositories",
            "4": "Harbor invite member to a project"
        },
        "dataset": {
            "DATASET_DOWNLOAD": "Download a dataset or a particular version of a dataset.",
            "DATASET_LIST": "List datasets belonging to logged in user.",
            "DATASET_SHOW_DETAIL": "Show details of a dataset.",
            "DATASET_VERSION": "Download a particular version of a dataset."
        },
        "project": {
            "PROJECT_LIST": "List accessible projects."
        },
        "user": {
            "USER_LOGIN": "For user to login.",
            "USER_LOGOUT": "For user to logout.",
            "USER_LOGOUT_CONFIRM": (
                "Input Y/yes to confirm you want to logout, otherwise input N/no to remain logged in."),
            "USER_LOGIN_USERNAME": "Specify username for login.",
            "USER_LOGIN_PASSWORD": "Specify password for login."
        },
        "file": {
            "FILE_ATTRIBUTE_LIST": "List attribute templates of a given Project.",
            "FILE_ATTRIBUTE_EXPORT": "Export attribute template from a given Project.",
            "FILE_LIST": "List files and folders inside a given Project/folder.",
            "FILE_SYNC": "Download files/folders from a given Project/folder/file in core zone.",
            "FILE_UPLOAD": "Upload files/folders to a given Project path.",
            "FILE_Z": "Target Zone (i.e., core/greenroom)  [default: greenroom]",
            "FILE_ATTRIBUTE_P": "Project Code",
            "FILE_ATTRIBUTE_N": "Attribute Template Name",
            "FILE_SYNC_ZIP": "Download files as a zip.",
            "FILE_SYNC_I": "Enable downloading by geid.",
            "FILE_SYNC_Z": "Target Zone (i.e., core/greenroom)",
            "FILE_UPLOAD_P": "Project folder path starting from Project code. (i.e., indoctestproject/user/folder)",
            "FILE_UPLOAD_A": "File Attribute Template used for annotating files during upload.",
            "FILE_UPLOAD_T": (
                "Add a tag to the file. This option could be used multiple times for adding multiple tags."),
            "FILE_UPLOAD_M": "The message used to comment on the purpose of uploading your processed file",
            "FILE_UPLOAD_S": "The Project path of the source file of your processed files.",
            "FILE_UPLOAD_PIPELINE": (
                "The processed pipeline of your processed files. [only used with '--source' option]"),
            "FILE_UPLOAD_ZIP": "Upload folder as a compressed zip file."
        },
        "config": {
            "SET_CONFIG": "Chose config file and set for cli.",
            "CONFIG_DESTINATION": "The destination the config file goes to, default will be current cli directory.",
        },
        "hpc": {
            "HPC_AUTH": "Authorize user to HPC with access token.",
            "HPC_LOGIN_HOST": "The host address for login HPC.",
            "HPC_LOGIN_USERNAME": "The username for login HPC.",
            "HPC_LOGIN_PASSWORD": "The password for login HPC.",
            "HPC_TOKEN": "The HPC token",
            "HPC_SUBMIT": "Submit a job to HPC",
            "HPC_JOB_INFO": "Get a job information",
            "HPC_NODES": "Get a list of nodes",
            "HPC_GET_NODE": "Get node information by node name",
            "HPC_PARTITIONS": "Get a list of partitions",
            "HPC_GET_PARTITION": "Get partition information by partition name"
        },
        "knowledge_graph": {
            "KG_IMPORT": "Import dataset schema into BlueBrainNexus ",
            "KG_DATASET_CODE": "The dataset code"
        },
        "container_registry": {
            "LIST_PROJECTS": "List all projects",
            "LIST_REPOSITORIES": "List all repositories (optionally: in a given project)",
            "CREATE_PROJECT": "Create a new project",
            "GET_SECRET": "Get your user CLI secret",
            "SHARE_PROJECT": "Share a project with another user"
        }
    }
