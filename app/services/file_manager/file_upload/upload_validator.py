# Copyright (C) 2022-2025 Indoc Systems
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
        source_ids = []
        if self.source:
            for source in self.source:
                _, source_path = source.split('/', 1)
                source_file_info = search_item(self.project_code, AppConfig.Env.green_zone.lower(), source_path)
                source_ids.append(source_file_info['result'].get('id'))
                if not source_file_info:
                    SrvErrorHandler.customized_handle(ECustomizedError.INVALID_SOURCE_FILE, True, value=self.source)
        return source_ids

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
        loaded_attribute = {}
        if self.attribute:
            loaded_attribute = self.validate_attribute()
        if self.tag:
            self.validate_tag()
        source_ids = self.validate_zone()
        converted_content = {'source_file': source_ids, 'attribute': loaded_attribute}
        return converted_content
