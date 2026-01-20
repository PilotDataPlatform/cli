# Copyright (C) 2022-2026 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.


class INVALID_CHUNK_ETAG(Exception):
    chunk_number: int

    def __init__(self, chunk_number: int) -> None:
        super().__init__(f'Invalid ETag for chunk number {chunk_number}')

        self.chunk_number = chunk_number
