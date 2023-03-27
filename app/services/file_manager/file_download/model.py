# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

from enum import Enum


class EFileStatus(Enum):
    WAITING = 'WAITING'
    RUNNING = 'RUNNING'
    SUCCEED = 'SUCCEED'
    FAILED = 'FAILED'

    def __str__(self):
        return '%s' % self.name
