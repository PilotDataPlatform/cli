# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from enum import Enum


class EFileStatus(str, Enum):
    WAITING = 'WAITING'
    RUNNING = 'RUNNING'
    SUCCEED = 'SUCCEED'
    FAILED = 'FAILED'
