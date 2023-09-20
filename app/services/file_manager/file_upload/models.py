# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import math
from enum import Enum
from os.path import basename
from os.path import dirname
from os.path import getsize
from typing import List
from typing import Tuple

from tqdm import tqdm

from app.configs.app_config import AppConfig


class UploadType(Enum):
    AS_FILE = 'AS_FILE'
    AS_FOLDER = 'AS_FOLDER'

    def __str__(self):
        return self.name


class ItemStatus(str, Enum):
    """
    Summary:
        Enum type for item status where:
            - REGISTERED means file is created by upload service but not complete yet. either in progress or fail.
            - ACTIVE means file uploading is complete.
            - ARCHIVED means the file has been deleted
        The status will be stored at metadata table.
    """

    REGISTERED = 'REGISTERED'
    ACTIVE = 'ACTIVE'
    ARCHIVED = 'ARCHIVED'

    def __str__(self):
        return self.name


class FileObject:
    """
    Summary:
        The class contains file infomation
    """

    resumable_id: str
    job_id: str
    item_id: str
    parent_path: str
    file_name: str

    local_path: str
    total_size: int
    total_chunks: int

    uploaded_chunks: List[dict]

    progress_bar = None

    def __init__(
        self,
        object_path: str,
        local_path: str,
        resumable_id: str = None,
        job_id: str = None,
        item_id: str = None,
    ) -> None:
        self.resumable_id = resumable_id
        self.job_id = job_id
        self.item_id = item_id
        self.object_path = object_path
        self.parent_path, self.file_name = dirname(object_path), basename(object_path)

        self.local_path = local_path
        self.total_size, self.total_chunks = self.generate_meta(local_path)

        self.uploaded_chunks = {}

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

    def update_progress(self, chunk_size: int) -> None:
        """
        Summary:
            The function is to update the progress bar
        Parameter:
            - chunk_size(int): the size of a chunk
        """
        if self.progress_bar is None:
            self.progress_bar = tqdm(
                total=self.total_size,
                leave=True,
                bar_format='{desc} |{bar:30} {percentage:3.0f}% {remaining}',
            )
            self.progress_bar.set_description(f'Uploading {self.file_name}')

        self.progress_bar.update(chunk_size)
        self.progress_bar.refresh()

    def close_progress(self) -> None:
        """
        Summary:
            The function is to close the progress bar
        """
        if self.progress_bar is not None:
            self.progress_bar.clear()
            self.progress_bar.close()
            self.progress_bar = None
