# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import json
from os import makedirs
from os.path import basename
from os.path import dirname
from os.path import exists
from os.path import join
from sys import exit
from typing import Any
from typing import Dict
from typing import List
from typing import Union

import click
from click.exceptions import Abort

import app.services.logger_services.log_functions as logger
import app.services.output_manager.message_handler as message_handler
from app.models.item import ItemType
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import customized_error_msg
from app.utils.aggregated import get_attribute_template_by_id
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
        general_folder: str,
        attribute_folder: str,
        tag_folder: str,
    ) -> None:
        """
        Summary:
            Initialize file metadata client.
        Parameters:
            zone (str): zone.
            file_path (str): file path.
            general_folder (str): local folder of general metadata eg. item_id, project_code.
            attribute_folder (str): local folder of attribute metadata.
            tag_folder (str): local folder of tag metadata.
        """

        self.zone = zone
        self.file_path = file_path
        self.project_code, self.object_path = self.file_path.split('/', 1)
        # only get the name regardless of the extension
        self.file_name = basename(self.object_path).rsplit('.', 1)[0]

        # location of metadata files
        self.general_location = join(general_folder, f'{self.file_name}-general.json')
        self.attribute_location = join(attribute_folder, f'{self.file_name}-attribute.json')
        self.tag_location = join(tag_folder, f'{self.file_name}-tag.json')
        self._check_duplication(self.general_location, self.attribute_location, self.tag_location)

    def _check_duplication(self, general_loc: str, attribute_loc: str, tag_loc: str) -> None:
        """
        Summary:
            Check if the metadata files already exist in location system
            and ask user whether to overwrite.
        """

        file_dict = {'general': general_loc, 'attribute': attribute_loc, 'tag': tag_loc}

        # check if the manifest file exists and ask user whether to overwrite
        try:
            duplicate_error = customized_error_msg(ECustomizedError.LOCAL_METADATA_FILE_EXISTS)
            overwrite_check = False
            for metadata_name, location in file_dict.items():
                if exists(location):
                    overwrite_check = True
                    duplicate_error = duplicate_error + f'\n - {metadata_name}: {location}'

            if overwrite_check:
                duplicate_error = duplicate_error + '\nDo you want to overwrite the existing file?'
                click.confirm(duplicate_error, abort=True)
        except Abort:
            message_handler.SrvOutPutHandler.cancel_metadata_download()
            exit(1)

    def save_file_metadata(self, file_loc: str, metadata: Union[dict, list]) -> None:
        """
        Summary:
            Save file metadata to local file.
        """

        makedirs(dirname(file_loc), exist_ok=True)
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
        root_folder, object_path = object_path.split('/', 1)
        root_type = ItemType.get_type_from_keyword(root_folder)
        object_path = join(root_type.get_prefix_by_type(), object_path)
        item_res = search_item(project_code, self.zone, object_path)
        if item_res.get('code') == 404:
            logger.error(f'Cannot find item {self.file_path} at {self.zone}.')
            exit(1)

        # filter out item metadata
        item_res = item_res.get('result', {})
        extra_info = item_res.pop('extended', {}).get('extra')
        tags = extra_info.get('tags', [])
        attributes = extra_info.get('attributes', {})
        # use the uuid of attribute template to get template name
        attribute_info = {}
        if len(attributes):
            template_uuid = next(iter(attributes))
            attribute_name = get_attribute_template_by_id(template_uuid).get('name')
            attribute_detail = attributes.get(template_uuid)
            attribute_info = {attribute_name: attribute_detail}
            self.save_file_metadata(self.attribute_location, attribute_info)
        else:
            logger.warning('No attribute metadata found.')

        # save metadata into files
        self.save_file_metadata(self.general_location, item_res)
        self.save_file_metadata(self.tag_location, tags)

        return item_res, attribute_info, tags
