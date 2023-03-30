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

from tqdm import tqdm

from app.configs.app_config import AppConfig


class UploadType(Enum):
    AS_FILE = 'AS_FILE'
    AS_FOLDER = 'AS_FOLDER'

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

    # progress bar object
    progress_bar = None

    def __init__(
        self, resumable_id: str, job_id: str, item_id: str, object_path: str, local_path: str, uploaded_chunks: List
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
