# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import json
from typing import Any
from typing import Dict
from typing import List
from typing import Union

from app.utils.aggregated import search_item


class FileMetaClient:
    """
    Summary:
        A client for interacting with file metadata. currently support to download
        file metadata from metadata service.
    """

    def __init__(
        self,
        zone: str,
        file_path: str,
        general_location: str,
        attribute_location: str,
        tag_location: str,
    ) -> None:
        """
        Summary:
            Initialize file metadata client.
        Parameters:
            zone (str): zone.
            file_path (str): file path.
            general_location (str): local file location of general metadata eg. item_id, project_code.
            attribute_location (str): local file location of attribute metadata.
            tag_location (str): local file location of tag metadata.
        """

        self.zone = zone
        self.file_path = file_path
        self.project_code, self.object_path = self.file_path.split('/', 1)

        # location of metadata files
        self.general_location = general_location
        self.attribute_location = attribute_location
        self.tag_location = tag_location

    def save_file_metadata(self, file_loc: str, metadata: Union[dict, list]) -> None:
        """
        Summary:
            Save file metadata to local file.
        """

        with open(file_loc, 'w') as f:
            json.dump(metadata, f, indent=4)

    def download_file_metadata(self) -> List[Dict[str, Any]]:
        """
        Summary:
            Download file metadata from metadata service, including.
        Returns:
            item_res (Dict[str, Any]): general metadata of file.
            attribute_detail (Dict[str, Any]): attribute metadata of file.
            tags (List[str]): tags metadata of file.
        """

        project_code, object_path = self.file_path.split('/', 1)
        item_res = search_item(project_code, self.zone, object_path, 'file').get('result', {})
        extra_info = item_res.pop('extended', {}).get('extra')
        tags = extra_info.get('tags', [])
        attributes = extra_info.get('attributes', [])
        # remove the uuid of attribute template
        attribute_detail = attributes.get(next(iter(attributes)))

        # save metadata into files
        self.save_file_metadata(self.general_location, item_res)
        self.save_file_metadata(self.attribute_location, attribute_detail)
        self.save_file_metadata(self.tag_location, tags)

        return item_res, attribute_detail, tags
