# Copyright (C) 2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

from enum import Enum


class LoginMethod(str, Enum):
    """Available login methods."""

    API_KEY = 'api-key'
    DEVICE_CODE = 'device-code'
