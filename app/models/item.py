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

    @classmethod
    def get_type_from_keyword(self, keyword: str):
        """The function will return the type of the item based on the keyword.

        - name folder will have keyword 'namefolder' as input
        - project folder will not have any keyword
        """

        alternative_mapping = {
            'shared': self.SHAREDFOLDER,
            'users': self.NAMEFOLDER,
        }

        return alternative_mapping.get(keyword, self.NAMEFOLDER)

    def get_prefix_by_type(self) -> str:
        """Get the prefix for the folder type."""

        prefix = {
            self.NAMEFOLDER: 'users/',
            self.SHAREDFOLDER: 'shared/',
        }

        return prefix.get(self.value, '')
