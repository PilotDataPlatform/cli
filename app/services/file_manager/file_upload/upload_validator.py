# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from typing import Any
from typing import Dict
from typing import List

from app.configs.app_config import AppConfig
from app.services.file_manager.file_manifests import SrvFileManifests
from app.services.file_manager.file_tag import SrvFileTag
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.utils.aggregated import search_item


class UploadEventValidator:
    def __init__(self, project_code: str, zone: str, source: str, attribute: Dict[str, Any], tag: List[str]):
        self.project_code = project_code
        self.zone = zone
        self.source = source
        self.attribute = attribute
        self.tag = tag

    def validate_zone(self):
        source_file_info = {}
        if self.source:
            source_file_info = search_item(self.project_code, AppConfig.Env.core_zone.lower(), self.source)
            source_file_info = source_file_info['result']
            if not source_file_info:
                SrvErrorHandler.customized_handle(ECustomizedError.INVALID_SOURCE_FILE, True, value=self.source)
        return source_file_info

    def validate_attribute(self):
        srv_manifest = SrvFileManifests()
        try:
            attribute = srv_manifest.convert_import(self.attribute, self.project_code)
            srv_manifest.validate_manifest(attribute)
            return attribute
        except Exception:
            SrvErrorHandler.customized_handle(ECustomizedError.INVALID_TEMPLATE, True)

    def validate_tag(self):
        srv_tag = SrvFileTag()
        srv_tag.validate_taglist(self.tag)

    def validate_upload_event(self):
        source_file_info, loaded_attribute = {}, {}
        if self.attribute:
            loaded_attribute = self.validate_attribute()
        if self.tag:
            self.validate_tag()
        if self.zone == AppConfig.Env.core_zone.lower():
            source_file_info = self.validate_zone()
        converted_content = {'source_file': source_file_info, 'attribute': loaded_attribute}
        return converted_content
