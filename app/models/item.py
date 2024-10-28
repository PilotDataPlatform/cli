# Copyright (C) 2023-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from enum import Enum


class ItemType(str, Enum):
    """The class to reflect the type of item in database."""

    FILE = 'file'
    FOLDER = 'folder'
    NAMEFOLDER = 'name_folder'
    SHAREDFOLDER = 'project_folder'
    ROOTFOLDER = 'root_folder'
    TRASH = 'trash'

    @classmethod
    def get_type_from_keyword(self, keyword: str):
        """The function will return the type of the item based on the keyword.

        - name folder will have keyword 'namefolder' as input
        - project folder will not have any keyword
        """

        alternative_mapping = {
            'shared': self.SHAREDFOLDER,
            'users': self.NAMEFOLDER,
            'trash': self.TRASH,
        }

        return alternative_mapping.get(keyword, self.FOLDER)

    def get_prefix_by_type(self) -> str:
        """Get the prefix for the folder type."""

        prefix = {
            self.NAMEFOLDER: 'users/',
            self.SHAREDFOLDER: 'shared/',
            self.ROOTFOLDER: '',
            self.TRASH: '',
        }

        return prefix.get(self.value, '')


class ItemZone(str, Enum):
    GREENROOM = 'greenroom'
    CORE = 'core'


class ItemStatus(str, Enum):
    # the new enum type for file status
    # - REGISTERED means file is created by upload service
    #   but not complete yet. either in progress or fail.
    # - ACTIVE means file uploading is complete.
    # - TRASHED means the file has been moved to trash bin.
    # - DELETED means the file has been permanently deleted.

    REGISTERED = 'REGISTERED'
    ACTIVE = 'ACTIVE'
    TRASHED = 'TRASHED'
    DELETED = 'DELETED'

    def __str__(self) -> str:
        return str(self.name)
