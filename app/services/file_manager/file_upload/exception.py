# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.


class INVALID_CHUNK_ETAG(Exception):
    chunk_number: int

    def __init__(self, chunk_number: int) -> None:
        self.chunk_number = chunk_number
