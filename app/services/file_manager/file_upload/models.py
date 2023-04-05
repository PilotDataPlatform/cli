# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

import math
from enum import Enum
from os.path import basename
from os.path import dirname
from os.path import getsize
from typing import List
from typing import Tuple

from app.configs.app_config import AppConfig


class UploadType(Enum):
    AS_FILE = 'AS_FILE'
    AS_FOLDER = 'AS_FOLDER'

    def __str__(self):
        return '%s' % self.name


class ItemStatus(str, Enum):
    # the new enum type for file status

    REGISTERED = 'REGISTERED'  # file is created by upload service but not complete yet. either in progress or fail.
    ACTIVE = 'ACTIVE'  # file uploading is complete.
    ARCHIVED = 'ARCHIVED'  # the file has been deleted

    def __str__(self):
        return '%s' % self.name


class FileObject:
    """
    Summary:
        The class contains file infomation
    """

    # object storage info
    resumable_id: str
    job_id: str
    item_id: str
    parent_path: str
    file_name: str

    # local file info
    local_path: str
    total_size: int
    total_chunks: int

    # resumable info
    uploaded_chunks: List[dict]

    def __init__(
        self,
        object_path: str,
        local_path: str,
        uploaded_chunks: List,
        resumable_id: str = None,
        job_id: str = None,
        item_id: str = None,
    ) -> None:
        # object storage info
        self.resumable_id = resumable_id
        self.job_id = job_id
        self.item_id = item_id
        self.object_path = object_path
        self.parent_path, self.file_name = dirname(object_path), basename(object_path)

        # local file info
        self.local_path = local_path
        self.total_size, self.total_chunks = self.generate_meta(local_path)

        # resumable info
        self.uploaded_chunks = uploaded_chunks

    def generate_meta(self, local_path: str) -> Tuple[int, int]:
        """
        Summary:
            The function is to generate chunk upload meatedata for a file.
        Parameter:
            - input_path: The path of the local file eg. a/b/c.txt.
        return:
            - total_size: the size of file
            - total_chunks: the number of chunks will be uploaded.
        """
        file_length_in_bytes = getsize(local_path)
        total_size = file_length_in_bytes
        total_chunks = math.ceil(total_size / AppConfig.Env.chunk_size)
        return total_size, total_chunks

    def to_dict(self):
        """
        Summary:
            The function is to convert the object to json format.
        return:
            - json format of the object.
        """
        return {
            'resumable_id': self.resumable_id,
            'job_id': self.job_id,
            'item_id': self.item_id,
            'object_path': self.object_path,
            'local_path': self.local_path,
            'total_size': self.total_size,
            'total_chunks': self.total_chunks,
            'uploaded_chunks': self.uploaded_chunks,
        }
