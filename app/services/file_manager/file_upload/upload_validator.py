# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from app.configs.app_config import AppConfig
from app.services.file_manager.file_manifests import SrvFileManifests
from app.services.file_manager.file_tag import SrvFileTag
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.utils.aggregated import search_item


class UploadEventValidator:
    def __init__(self, project_code, zone, upload_message, source, process_pipeline, token, attribute, tag):
        self.project_code = project_code
        self.zone = zone
        self.upload_message = upload_message
        self.source = source
        self.process_pipeline = process_pipeline
        self.token = token
        self.attribute = attribute
        self.tag = tag

    def validate_zone(self):
        source_file_info = {}
        if not self.upload_message:
            SrvErrorHandler.customized_handle(
                ECustomizedError.INVALID_UPLOAD_REQUEST, True, value='upload-message is required'
            )
        if self.source:
            if not self.process_pipeline:
                SrvErrorHandler.customized_handle(
                    ECustomizedError.INVALID_UPLOAD_REQUEST, True, value='process pipeline name required'
                )
            else:
                source_file_info = search_item(self.project_code, AppConfig.Env.green_zone.lower(), self.source, 'file')
                source_file_info = source_file_info['result']
                if not source_file_info:
                    SrvErrorHandler.customized_handle(ECustomizedError.INVALID_SOURCE_FILE, True, value=self.source)
        return source_file_info

    def validate_attribute(self):
        srv_manifest = SrvFileManifests()
        if not os.path.isfile(self.attribute):
            raise Exception('Attribute not exist in the given path')
        try:
            attribute = srv_manifest.read_manifest_template(self.attribute)
            attribute = srv_manifest.convert_import(attribute, self.project_code)
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
