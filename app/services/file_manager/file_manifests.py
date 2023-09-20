# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import json

import requests

import app.services.output_manager.message_handler as message_handler
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.service_meta_class import MetaService
from app.services.output_manager.error_handler import ECustomizedError
from app.services.output_manager.error_handler import SrvErrorHandler
from app.services.user_authentication.decorator import require_valid_token


def dupe_checking_hook(pairs):
    result = {}
    for key, val in pairs:
        if key in result:
            raise KeyError('Duplicate attribute specified: %s' % key)
        result[key] = val
    return result


decoder = json.JSONDecoder(object_pairs_hook=dupe_checking_hook)


class SrvFileManifests(metaclass=MetaService):
    app_config = AppConfig()
    user = UserConfig()

    def __init__(self, interactive=True):
        self.interactive = interactive

    @staticmethod
    def read_manifest_template(path):
        with open(path, 'r') as file:
            data = file.read()
        decoder.decode(data)
        obj = json.loads(data)
        return obj

    @require_valid_token()
    def validate_template(self, manifest_json):
        url = self.app_config.Connections.url_bff + '/v1/validate/manifest'
        headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
        }
        res = requests.post(url, headers=headers, json=manifest_json)
        res_json = res.json()
        code = res_json.get('code')
        if code == 200:
            result = res_json['result']
            message_handler.SrvOutPutHandler.file_manifest_validation(result)
            return result == 'valid', res_json
        elif code == 403:
            SrvErrorHandler.customized_handle(ECustomizedError.CODE_NOT_FOUND, self.interactive)
        else:
            return False, res_json

    @require_valid_token()
    def attach(self, manifest_json: dict, file_name: str, zone: str):
        url = self.app_config.Connections.url_bff + '/v1/manifest/attach'
        manifest_json['file_name'] = file_name
        manifest_json['zone'] = zone
        headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
        }
        res = requests.post(url, headers=headers, json=manifest_json)
        if res.status_code == 200:
            result = res.json()
            result['code'] = res.status_code
            return result
        else:
            return res.json()

    @require_valid_token()
    def list_manifest(self, project_code):
        get_url = self.app_config.Connections.url_bff + '/v1/manifest'
        headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
        }
        params = {'project_code': project_code}
        res = requests.get(get_url, params=params, headers=headers)
        return res

    @require_valid_token()
    def export_manifest(self, project_code, attribute_name):
        get_url = AppConfig.Connections.url_bff + '/v1/manifest/export'
        headers = {
            'Authorization': 'Bearer ' + self.user.access_token,
        }
        params = {'project_code': project_code, 'name': attribute_name}
        res = requests.get(get_url, params=params, headers=headers)
        result = res.json().get('result')
        code = res.json().get('code')
        if code == 404:
            SrvErrorHandler.customized_handle(ECustomizedError.MANIFEST_NOT_EXIST, True, value=attribute_name)
        elif code == 403:
            SrvErrorHandler.customized_handle(ECustomizedError.CODE_NOT_FOUND, True)
        else:
            return result

    def export_template(self, project_code, manifest_def):
        manifest_name = manifest_def.get('name')
        manifest_template_path = '{}_{}_template.json'.format(project_code, manifest_name)
        manifest_definition_path = '{}_{}_definition.json'.format(project_code, manifest_name)
        with open(manifest_definition_path, 'w') as outfile1:
            json.dump(manifest_def, outfile1, indent=4, sort_keys=False)
        converted_template = self.convert_export(manifest_def)
        with open(manifest_template_path, 'w') as outfile2:
            json.dump(converted_template, outfile2, indent=4, sort_keys=False)
        return manifest_template_path, manifest_definition_path

    @staticmethod
    def convert_import(user_defined: dict, project_code):
        # convert the user defined json file to attach post json
        converted_attrs = {}
        keys = list(user_defined.keys())
        mani_name = keys[0]
        attrs = user_defined[mani_name]
        for key in attrs:
            converted_attrs[key] = attrs[key]
        return {'manifest_name': mani_name, 'project_code': project_code, 'attributes': converted_attrs}

    @staticmethod
    def convert_export(attach_post: dict):
        # convert the attach post json to user defined json
        converted = {}
        name = attach_post['name']
        converted[name] = {}
        for attr in attach_post['attributes']:
            converted[name][attr['name']] = ''
        return converted

    def validate_manifest(self, manifest, raise_error=True):
        manifest_validation_event = {'manifest_json': manifest}
        validation = self.validate_template(manifest_validation_event)
        if not validation[0]:
            validation_result = validation[1].get('error_msg').split(' ')
            error_attr = '_'.join(validation_result[:-1]).upper()
            validation_error = getattr(ECustomizedError, error_attr)
            SrvErrorHandler.customized_handle(validation_error, raise_error, validation_result[-1])
        else:
            validation = [True]
            validation_error = ''
        return validation, validation_error

    def attach_manifest(self, manifest: dict, file_name: str, zone: str):
        res = self.attach(manifest, file_name, zone)
        if res.get('code') != 200:
            error = res.get('error_msg')
            if self.interactive:
                file_attached = False
                attach_error = error
                SrvErrorHandler.default_handle('Attribute Attach Failed: ' + error, True)
            else:
                SrvErrorHandler.default_handle('Attribute Attach Failed: ' + error, False)
                file_attached = False
                attach_error = error
        else:
            message_handler.SrvOutPutHandler.attach_manifest()
            file_attached = True
            attach_error = ''
        return file_attached, attach_error
