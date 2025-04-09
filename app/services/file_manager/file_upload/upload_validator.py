# Copyright (C) 2022-2025 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

from typing import Any
from typing import Dict
from typing import List

from app.services.file_manager.file_manifests import SrvFileManifests
from app.services.file_manager.file_tag import SrvFileTag
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.utils.aggregated import search_item


class UploadEventValidator:
    def __init__(self, project_code: str, source_zone: str, source: str, attribute: Dict[str, Any], tag: List[str]):
        self.project_code = project_code
        self.source_zone = source_zone
        self.source = source
        self.attribute = attribute
        self.tag = tag

    def validate_zone(self):
        source_ids = []
        if self.source:
            for source in self.source:
                _, source_path = source.split('/', 1)
                source_file_info = search_item(self.project_code, self.source_zone, source_path)
                if not source_file_info['result']:
                    SrvErrorHandler.customized_handle(
                        ECustomizedError.INVALID_SOURCE_ITEM, True, value=(source, self.source_zone)
                    )
                source_ids.append(source_file_info['result'].get('id'))

            # check if there is any duplication source id
            if len(source_ids) != len(set(source_ids)):
                SrvErrorHandler.customized_handle(
                    ECustomizedError.INVALID_UPLOAD_REQUEST,
                    value=('Source file list contains duplication',),
                    if_exit=True,
                )
        return source_ids

    def validate_attribute(self):
        '''
        Summary:
            function will check if the attribute exists. And parse the
            attribute to the correct format with manifest id.
        Return:
            attribute: dict, the attribute with manifest id
            id: str, the manifest id
        '''
        srv_manifest = SrvFileManifests()
        try:
            manifest = srv_manifest.convert_import(self.attribute, self.project_code)
            res = srv_manifest.list_manifest(self.project_code, manifest.get('manifest_name'))
            manifest_id = res.json().get('result')[0].get('id')

            attribute = {
                'id': manifest_id,
                'attributes': manifest.get('attributes'),
            }
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
