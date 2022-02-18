from env import ENVAR
class HelpPage:
    page = {
    "update": {
        "version": "1.7.0",
        "1": "HPC job command to submit job and check job status.",
        "2": "HPC node command to list nodes and get node status.",
        "3": "HPC partition command to list partitions and get partition status"
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
        "USER_LOGOUT_CONFIRM": "Input Y/yes to confirm you want to logout, otherwise input N/no to remain logged in.",
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
        "FILE_SYNC_I" : "Enable downloading by geid.",
        "FILE_SYNC_Z": "Target Zone (i.e., core/greenroom)",
        "FILE_UPLOAD_P": "Project folder path starting from Project code. (i.e., indoctestproject/user/folder)",
        "FILE_UPLOAD_G": f"{ENVAR.dicom_project} ID (Only used by {ENVAR.dicom_project.upper()} Project)",
        "FILE_UPLOAD_A": "File Attribute Template used for annotating files during upload.",
        "FILE_UPLOAD_T": "Add a tag to the file. This option could be used multiple times for adding multiple tags.",
        "FILE_UPLOAD_M": "The message used to comment on the purpose of uploading your processed file",
        "FILE_UPLOAD_S": "The Project path of the source file of your processed files.",
        "FILE_UPLOAD_PIPELINE": "The processed pipeline of your processed files. [only used with '--source' option]",
        "FILE_UPLOAD_ZIP": "Upload folder as a compressed zip file."
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
        "LIST_PROJECTS" : "List all public projects in Harbor",
        "LIST_REPOSITORIES" : "List all repositories (optionally: in a given Harbor project)",
        "CREATE_PROJECT" : "Create a new project",
        "GET_SECRET": "Get your user CLI secret",
        "INVITE_MEMBER": "Invite another Platform user into a Harbor Project"
    }
}
    
