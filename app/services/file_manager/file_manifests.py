from app.models.service_meta_class import MetaService
from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
import json
import requests
from app.services.output_manager.error_handler import ECustomizedError, SrvErrorHandler
import app.services.logger_services.log_functions as logger
from app.services.user_authentication.decorator import require_valid_token
import app.services.output_manager.message_handler as message_handler


class SrvFileManifests(metaclass=MetaService):
    app_config =  AppConfig()
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
        url = self.app_config.Connections.url_bff + "/v1/validate/manifest"
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
        }
        res = requests.post(url, headers=headers, json=manifest_json)
        if res.status_code == 200:
            result = res.json()['result']
            message_handler.SrvOutPutHandler.file_manifest_validation(result)
            return result == 'Valid', res.json()
        else:
            return False, res.json()

    @require_valid_token()
    def attach(self, manifest_json, file_name, zone):
        url = self.app_config.Connections.url_bff + "/v1/manifest/attach"
        manifest_json['file_name'] = file_name
        manifest_json['zone'] = zone
        manifest_json = {'manifest_json': manifest_json}
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
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
        get_url = self.app_config.Connections.url_bff + "/v1/manifest"
        headers = {
            'Authorization': "Bearer " + self.user.access_token,
        }
        params = {'project_code': project_code}
        res = requests.get(get_url, params=params, headers=headers)
        return res

    def export_template(self, manifest_name, project_code, manifest_def):
        # will export 2 files: manifest_template and manifest_definition
        manifest_template_path = '{}_{}_template.json'.format(project_code, manifest_name)
        manifest_definition_path = '{}_{}_definition.json'.format(project_code, manifest_name)
        # export definition
        with open(manifest_definition_path, 'w') as outfile1:
            json.dump(manifest_def, outfile1, indent=4, sort_keys=False)
        # export template
        converted_template = self.convert_export(manifest_def)
        with open(manifest_template_path, 'w') as outfile2:
            json.dump(converted_template, outfile2, indent=4, sort_keys=False)
        return manifest_template_path, manifest_definition_path

    @staticmethod
    def convert_import(user_defined: dict, project_code):
        # convert the user defined json file to attach post json
        converted_attrs = {}
        keys = [key for key in user_defined]
        mani_name = keys[0]
        attrs = user_defined[mani_name]
        for key in attrs:
            converted_attrs[key] = attrs[key]
        return {
            "manifest_name": mani_name,
            "project_code": project_code,
            "attributes": converted_attrs
        }
    
    @staticmethod
    def convert_export(attach_post: dict):
        # convert the attach post json to user defined json
        converted = {}
        name = attach_post['manifest_name']
        converted[name] = {}
        for attr in attach_post['attributes']:
            converted[name][attr['name']] = ''
        return converted

    def void_validate_manifest(self, manifest, raise_error=True):
        manifest_validation_event = {'manifest_json': manifest}
        validation = self.validate_template(manifest_validation_event)
        if not validation[0]:
            validation_result = validation[1].get('result').split(' ')
            error_attr = '_'.join(validation_result[:-1]).upper()
            validation_error = getattr(ECustomizedError, error_attr)
            SrvErrorHandler.customized_handle(validation_error, raise_error, validation_result[-1])
        else:
            validation = [True]
            validation_error = ''
        return validation, validation_error

    def attach_manifest(self, manifest, file_name, zone):
        res = self.attach(manifest, file_name, zone)
        if res.get('code') != 200:
            error = res.get('error_msg')
            if self.interactive:
                file_attached = False
                attach_error = error
                SrvErrorHandler.default_handle("Attribute Attach Failed: " + error, True)
            else:
                SrvErrorHandler.default_handle("Attribute Attach Failed: " + error, False)
                file_attached = False
                attach_error = error
        else:
            message_handler.SrvOutPutHandler.attach_manifest()
            file_attached = True
            attach_error = ''
        return file_attached, attach_error


def dupe_checking_hook(pairs):
    result = dict()
    for key, val in pairs:
        if key in result:
            raise KeyError("Duplicate attribute specified: %s" % key)
        result[key] = val
    return result


decoder = json.JSONDecoder(object_pairs_hook=dupe_checking_hook)
