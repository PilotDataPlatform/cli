# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.


class INVALID_CHUNK_ETAG(Exception):
    chunk_number: int

    def __init__(self, chunk_number: int) -> None:
        self.chunk_number = chunk_number
