# Copyright (C) 2023-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from enum import Enum


class FolderPrefix(str, Enum):
    """In database, name folders and project folders will prefix with different path. and user will need to key in the
    keyword to get the correct path. eg.

    - project folder:
        - key in: <project_code>/projectfolder/<folder_name>
        - path: <project_code>/shared/<folder_name>
    - name folder:
        - key in: <project_code>/<name>/<file>
        - path: <project_code>/<name>/<file>
    """

    NAMEFOLDER = 'namefolder'
    PROJECTFOLDER = 'projectfolder'

    def get_prefix(self) -> str:
        """Get the prefix for the folder type."""

        prefix = {
            'namefolder': '',
            'projectfolder': 'shared/',
        }

        return prefix.get(self.value)


class ItemType(str, Enum):
    """The class to reflect the type of item in database."""

    FILE = 'file'
    Folder = 'folder'
    NAMEFOLDER = 'name_folder'
    PROJECTFOLDER = 'project_folder'

    @classmethod
    def get_item_type(cls, value):
        # Define a mapping for alternative values
        alternative_mapping = {
            'namefolder': cls.NAMEFOLDER,
        }
        # Check if the value is in the alternative mapping
        if value in alternative_mapping:
            return alternative_mapping[value]
        # Fall back to normal lookup by value
        for item in cls:
            if item.value == value:
                return item
        return None
