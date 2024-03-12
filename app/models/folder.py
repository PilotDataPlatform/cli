# Copyright (C) 2023-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from enum import Enum


class FolderType(str, Enum):
    """Available folder types."""

    NAMEFOLDER = 'namefolder'
    PROJECTFOLDER = 'projectfolder'

    def get_prefix(self) -> str:
        """Get the prefix for the folder type."""

        prefix = {
            'namefolder': 'namefolder/',
            'projectfolder': 'shared/',
        }

        return prefix.get(self.value)
