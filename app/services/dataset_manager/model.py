# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from enum import Enum


class EFileStatus(Enum):
    WAITING = 'WAITING'
    RUNNING = 'RUNNING'
    SUCCEED = 'SUCCEED'
    FAILED = 'FAILED'

    def __str__(self):
        return '%s' % self.name
