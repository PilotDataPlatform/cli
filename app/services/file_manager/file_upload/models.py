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

import math
from enum import Enum
from os.path import basename, dirname, getsize
from typing import List, Tuple

from app.configs.app_config import AppConfig


class UploadType(Enum):
    AS_FILE = 'AS_FILE'
    AS_FOLDER = 'AS_FOLDER'

    def __str__(self):
        return '%s' % self.name


class FileObject:
    '''
    Summary:
        The class contains file infomation
    '''

    # object storage info
    resumable_id: str
    parent_path: str
    file_name: str

    # local file info
    local_path: str
    total_size: int
    total_chunks: int

    # resumable info
    uploaded_chunks: List[dict]

    def __init__(self, resumable_id: str, object_path: str, local_path: str, uploaded_chunks: List) -> None:
        # object storage info
        self.resumable_id = resumable_id
        self.object_path = object_path
        self.parent_path, self.file_name = dirname(object_path), basename(object_path)

        # local file info
        self.local_path = local_path
        self.total_size, self.total_chunks = self.generate_meta(local_path)

        # resumable info
        self.uploaded_chunks = uploaded_chunks

    def generate_meta(self, local_path: str) -> Tuple[int, int]:
        '''
        Summary:
            The function is to generate chunk upload meatedata for a file.
        Parameter:
            - input_path: The path of the local file eg. a/b/c.txt.
        return:
            - total_size: the size of file
            - total_chunks: the number of chunks will be uploaded.
        '''
        file_length_in_bytes = getsize(local_path)
        total_size = file_length_in_bytes
        total_chunks = math.ceil(total_size / AppConfig.Env.chunk_size)
        return total_size, total_chunks
