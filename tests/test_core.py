import unittest
import subprocess
import os
import json
import requests
import platform
from .test_config import ConfigClass
from .logger import Logger
os.environ['env'] = "dev"
from app.configs.user_config import AppConfig, UserConfig
from app.utils.aggregated import get_source_file, get_folder_in_project
from app.services.output_manager.error_handler import customized_error_msg, ECustomizedError
import time


# Remember to connect VPN before test

project = "pilot"
prepare_log = Logger(name='test_setup_teardown.log')
project_code = ConfigClass.project_code
manifest_name = ConfigClass.manifest_name
stamp = str(time.time())[0:10]
folder_name = "./tests/cmd_fd" + '_' + stamp + '/'
sub_folder_name = folder_name + "cmd_fd_layer2_" +stamp
single_file_1 = 'cmd_upload_test1_' + stamp
single_file_2 = 'cmd_upload_test2_' + stamp
lineage_target_file = 'cmd_lineage_test_base2_' + stamp
lineage_sample_file = 'cmd_lineage_test_file2_' + stamp
layer1_files = ['lay1_test_file1_' + stamp, 'lay1_test_file_' + stamp, 'lay1_test_file3_' + stamp]
layer2_files = ['lay2_test_file1_' + stamp, 'lay2_test_file2' + stamp, 'lay2_test_file3' + stamp]
manifest_template = f"{ConfigClass.project_code}_Manifest1_template.json"
manifest_definition = f"{ConfigClass.project_code}_Manifest1_definition.json"
non_exist_folder = 'cli_fd_' + stamp

linux = {
    "prod_app": f"pyinstaller -F --distpath ./app/bundled_app/linux --specpath ./app/build/linux --workpath ./app/build/linux --paths=./.venv/lib/python3.8/site-packages ./app/pilotcli.py -n {project}cli"
}

mac = {
    "prod_app": f"pyinstaller -F --distpath ./app/bundled_app/mac --specpath ./app/build/mac --workpath ./app/build/mac --paths=./.venv/lib/python3.8/site-packages ./app/pilotli.py -n {project}cli"
}

mac_arm = {
    "prod_app": f"pyinstaller -F --distpath ./app/bundled_app/mac_arm --specpath ./app/build/mac_arm --workpath ./app/build/mac_arm --paths=./.venv/lib/python3.8/site-packages ./app/{project}cli.py"
}

env = platform.system()
cpu = platform.processor()
lineage_url = ConfigClass.lineage_url

def setUpModule():
    if env == 'Darwin':
        if cpu == 'arm':
            create_file = "mkfile -n 1M"
            build_env = mac_arm
        else:
            create_file = "mkfile -n 1M"
            build_env = mac
    else:
        create_file = "fallocate -l 1M"
        build_env = linux
        
    for k, v in build_env.items():
        prepare_log.info(v)
        os.system(v)
    prepare_log.info(f'Test in system {env}')
    if not os.path.exists(folder_name):
        prepare_log.info(f'SetUpModule create folder {folder_name} and sub folder {sub_folder_name}')
        os.makedirs(folder_name)
        os.makedirs(sub_folder_name)
    if not os.path.exists(sub_folder_name):
        os.makedirs(sub_folder_name)
    prepare_log.info(f"Create files based on system {env}")
    for f in layer1_files:
        fname = folder_name + '/' + f
        if not os.path.isfile(fname):
            os.system(f"{create_file} {fname}")
    for f in layer2_files:
        sub_fname = sub_folder_name + '/' + f
        if not os.path.isfile(sub_fname):
            os.system(f"{create_file} {sub_fname}")
    if not os.path.isfile(single_file_1):
        os.system(f"{create_file} {single_file_1}")
    if not os.path.isfile(single_file_2):
        os.system(f"{create_file} {single_file_2}")
    if not os.path.isfile(lineage_target_file):
        os.system(f"{create_file} {lineage_target_file}")
    if not os.path.isfile(lineage_sample_file):
        os.system(f"{create_file} {lineage_sample_file}")
    if not os.path.isdir('./tests/download_test'):
        os.system('mkdir ./tests/download_test')


def tearDownModule():
    prepare_log.info("Removing local testing data")
    if os.path.exists(folder_name):
        prepare_log.info(f"RUN: rm -rf {folder_name}")
        os.system(f"rm -rf {folder_name}")
    if os.path.isfile(single_file_1):
        prepare_log.info(f"RUN: rm {single_file_1}")
        os.system(f"rm {single_file_1}")
    if os.path.isfile(single_file_2):
        prepare_log.info(f"RUN: rm {single_file_2}")
        os.system(f"rm {single_file_2}")
    if os.path.isfile(f"{manifest_definition}"):
        os.system(f"rm {manifest_definition}")
    if os.path.isfile(f"{manifest_template}"):
        os.system(f"rm {manifest_template}")
    if os.path.isfile(f"{lineage_target_file}"):
        os.system(f"rm {lineage_target_file}")
    if os.path.isfile(f"{lineage_sample_file}"):
        os.system(f"rm {lineage_sample_file}")
    if os.path.isdir('./tests/download_test'):
        os.system('rm -rf ./tests/download_test')

def get_bundled_app_dir():
    os = platform.system().lower()
    cpu = platform.processor().lower()
    if os == 'linux':
        return 'linux'
    elif os == 'darwin':
        if cpu == 'arm':
            return 'mac_arm'
        return 'mac'

class TestCommandsCore(unittest.TestCase):
    zone = AppConfig.Env.core_zone
    log = Logger(name='test_core.log')
    cmd_path = f"app/bundled_app/{get_bundled_app_dir()}/{project}cli"
    cmd_option = f"-z {zone} -m 'unit-test-upload-to-core'"
    line_width = 80
    pipeline = "cli-unit_test"
    file_list = []
    manifest_template = manifest_template
    core_folder = 'core-test'
    login_user = ConfigClass.platform_user.get('username')



    @classmethod
    def get_file_info(cls, file_path):
        cls.log.info(f"Check file in project {project_code}/{cls.zone}: {file_path}")
        user = UserConfig()
        token = user.access_token
        try:
            res = get_source_file(file_path, project_code,
                                  token, namespace=cls.zone)
            cls.log.info(f"Check respone: {res}")
            return res
        except Exception as e:
            cls.log.error(f"Getting file error: {e}")
            raise e

    @classmethod
    def delete_files(cls, delete_list, token):
        cls.log.info(f"DELETING {delete_list}".ljust(80, '-'))
        try:
            geid_to_delete = [{'geid': geid} for geid in delete_list]
            delete_url = ConfigClass.tear_down_url
            payload = {
                "payload": {
                    "targets": geid_to_delete},
                "operator": "jzhang21",
                "operation": "delete",
                "project_geid": ConfigClass.project_geid,
                "session_id": "unittest-b2ee5b6e-7924-4f0f-b9c8-1a2ffb9835ca"
            }
            cls.log.info(f"Delete payload: {payload}")
            headers = {
                'Authorization': "Bearer " + token,
                'Session-ID': f'cli-unittest-' + stamp
            }
            res = requests.post(delete_url, headers=headers, json=payload)
            cls.log.info(f"API Response {res}")
            cls.log.info(f"API Reponse {res.text}")
            if res.status_code == 200 or res.status_code==202:
                response = res.json()
                cls.log.info(f"Delete {delete_list} Response: {response}")
            else:
                cls.log.error(f"Delete Failed: {res.text}")
                raise Exception(res.text)
        except Exception as e:
            cls.log.error(f'Error tear down: {e}')

    @classmethod
    def tearDownClass(cls):
        cls.log.info(f"{'Test tearDown'.center(cls.line_width, '=')}")
        user = UserConfig()
        token = user.access_token
        deleting_list = []
        try:
            file_list = [lineage_sample_file, lineage_target_file,
                        f"{cls.core_folder}/core1/core2/{lineage_target_file}",
                        f"{cls.core_folder}/core1/{lineage_sample_file}",
                        f"{cls.core_folder}/core1/{lineage_target_file}"]
            for f in file_list:
                cls.log.info(f'getting file info: {cls.login_user}/{f}')
                file_info = cls.get_file_info(f"{cls.login_user}/{f}")
                cls.log.info(f'File info: {file_info}')
                file_result = file_info
                if file_result == []:
                    return
                else:
                    cls.log.info(f'File result: {file_result}')
                    file_id = file_result[0].get('global_entity_id')
                    cls.log.info(f'File geid: {file_id}')
                    deleting_list.append(file_id)

            folder_res = get_folder_in_project(project_code, cls.zone,
                                            f"{cls.login_user}/{folder_name.split('/')[-2]}", token)
            cls.log.info(f'Folder response: {folder_res}')
            folder_geid = folder_res[0].get('global_entity_id')
            deleting_list.append(folder_geid)
        
            cls.log.warning(f'DELETING: {deleting_list}')
            _res = cls.delete_files(deleting_list, token)
            # delete_file(cls.zone)
        except Exception as e:
            cls.log.error(f"ERROR TearDown: {e}")
        finally:
            _cmd = f"{cls.cmd_path} user logout -y"
            res = subprocess.check_output(_cmd, shell=True)
            cls.log.info(f"\n{res.decode('ascii')}\n")

    def setUp(self):
        try:
            _cmd = f"{self.cmd_path} user login -U {self.login_user} " \
                   f"-P {ConfigClass.platform_user.get('password')}"
            self.log.info(_cmd)
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
        except Exception as e:
            raise e
        finally:
            if self.zone == 'greenroom':
                self.skip_condition = False
            else:
                self.skip_condition = True

    def tearDown(self):
        try:
            _cmd = f"{self.cmd_path} user logout -y"
            self.log.info(_cmd)
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
        except Exception as e:
            raise e

    def test_core_01_upload_file_with_invalid_pipe_capital(self):
        self.log.info(f"{'1 upload file to core with invalid pipe capital'.center(self.line_width, '=')}")
        invalid_pipe_name = "kSGmq8RCyMOZBwqzvIeM"
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user} ./{single_file_1} -t tag-1 -t tag2 " \
               f"{self.cmd_option} --pipeline {invalid_pipe_name}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res_out = p.communicate(input=b'y')[0]
            self.log.info(res_out.decode())
            self.assertIn(customized_error_msg(ECustomizedError.INVALID_PIPELINENAME), res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_1_upload_file_with_invalid_pipe_capital')

    def test_core_02_upload_file_with_invalid_pipe_too_long(self):
        self.log.info(f"{'2 upload file to core without invalid pipe too long'.center(self.line_width, '=')}")
        invalid_pipe_name = "ksgmq8rcymozbwqzviemw"
        self.log.info(f"Test with pipeline name with length {len(invalid_pipe_name)}")
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user} ./{single_file_1} -t tag-1 -t tag2 " \
               f"{self.cmd_option} --pipeline {invalid_pipe_name}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.INVALID_PIPELINENAME), res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_2_upload_file_with_invalid_pipe_too_long')

    def test_core_03_upload_file_with_invalid_pipe_characters(self):
        self.log.info(f"{'3 upload file to core with invalid pipe characters'.center(self.line_width, '=')}")
        invalid_pipe_list = ['~', '!', '@', '$', '%', '^', "'*'", '=',
                             '+', '[', '{', ']', '}', ':', ',', '/', '?']
        for char in invalid_pipe_list:
            self.log.info(char)
            _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user} ./{single_file_1} -t tag-1 -t tag2 " \
                   f"{self.cmd_option} --pipeline {char}"
            self.log.info(_cmd)
            try:
                p = subprocess.Popen(_cmd,
                                     stdout=subprocess.PIPE,
                                     stdin=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     shell=True)
                res = p.communicate(input=b'y')[0]
                self.log.info(f"\n{res.decode('ascii')}\n")
                self.assertIn(customized_error_msg(
                    ECustomizedError.INVALID_PIPELINENAME), res.decode())
            except Exception as e:
                self.log.error(e)
                raise Exception('test_core_3_upload_file_with_invalid_pipe_characters')

    def test_core_04_upload_file_without_message(self):
        self.log.info(f"{'4 upload file to core without message'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user} ./{single_file_1} -t tag-1 -t tag2 -z {AppConfig.Env.core_zone}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(
                ECustomizedError.INVALID_UPLOAD_REQUEST) % 'upload-message is required', res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_4_upload_file_without_message')

    def test_core_05_upload_file_with_source_without_pipeline(self):
        self.log.info(f"{'5 upload file to core with source file but no pipeline'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user} ./{single_file_1} -t tag-1 -t tag2 " \
               f"{self.cmd_option} -s {lineage_target_file}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(
                ECustomizedError.INVALID_UPLOAD_REQUEST) % 'process pipeline name required', res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_5_upload_file_with_source_without_pipeline')

    def test_core_06_upload_file_with_source_not_exist(self):
        self.log.info(f"{'6 upload file to core with source file not exist'.center(self.line_width, '=')}")
        invalid_src = "random_fake_data_that_not_exist_in_core"
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user} ./{single_file_1} -t tag-1 -t tag2 " \
               f"{self.cmd_option} -s {invalid_src} --pipeline {self.pipeline}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(
                ECustomizedError.INVALID_SOURCE_FILE) % invalid_src, res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_6_upload_file_with_source_not_exist')

    def get_lineage(self, upload_file_path, custom_param=None):
        url = lineage_url
        user = UserConfig()
        token = user.access_token
        res = self.get_file_info(upload_file_path)
        result = res[0]
        file_geid = result.get('global_entity_id')
        if custom_param:
            params = custom_param
            params['geid'] = file_geid
        else:
            params = {"geid": file_geid,
                      "direction": "INPUT",
                      "type_name": "file_data"}
        headers = {
            'Authorization': "Bearer " + token,
        }
        self.log.info(f"Lineage params: {params}")
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 200:
            res = res.json()
            self.log.info(f"lineage res: {res}")
            entity_map = res.get('result').get('guidEntityMap')
            entity_list = list(entity_map.keys())
            self.log.info(f"entity_map: {entity_map}")
            self.log.info(f"entity_list: {entity_list}")
            ordered_entity = {'relation': res.get('result').get('relations')}
            attr_1 = entity_map.get(entity_list[0])
            attr_2 = entity_map.get(entity_list[1])
            attr_3 = entity_map.get(entity_list[2])
            base_entity_id = res.get('result').get('baseEntityGuid')
            attr_list = [attr_1, attr_2, attr_3]
            for a in attr_list:
                current_guid = a.get('guid', None)
                attr_type = a.get('typeName')
                attr = a.get("attributes")
                if attr_type == 'file_data':
                    if current_guid == base_entity_id:
                        ordered_entity['start'] = attr.get("name")
                        ordered_entity['start_id'] = current_guid
                    else:
                        ordered_entity['end'] = attr.get("name")
                        ordered_entity['end_id'] = current_guid
                else:
                    ordered_entity['mid'] = attr.get("name")
                    ordered_entity['mid_id'] = current_guid
            return ordered_entity
        else:
            self.log.error(res.text)
            return None

    def test_core_07_upload_file_without_source(self):
        self.log.info(f"{'7 upload file to core without source file'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user} ./{lineage_target_file} -t tag-1 -t tag2 " \
               f"{self.cmd_option}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res.decode()}\n")
            self.assertIn(b"All files uploaded successfully.", res)
            self.file_list.append(lineage_target_file)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_7_upload_file_without_source')

    def test_core_08_contributor_upload(self):
        self.log.info(f"{'8 contributor upload to core'.center(self.line_width, '=')}")
        login_cmd = f"{self.cmd_path} user login -U {ConfigClass.project_contributor.get('username')} " \
               f"-P {ConfigClass.project_contributor.get('password')}"
        self.log.info(login_cmd)
        upload_cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user} ./{lineage_sample_file} -t tag-1 -t tag2 " \
                     f"{self.cmd_option} -s {self.login_user}/{lineage_target_file} --pipeline {self.pipeline}"
        self.log.info(upload_cmd)
        try:
            login_p = subprocess.Popen(login_cmd,
                                       stdout=subprocess.PIPE,
                                       stdin=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       shell=True)
            login_res = login_p.communicate(input=b'y')[0]
            self.log.info(f"\n{login_res.decode('ascii')}\n")

            p_upload = subprocess.Popen(upload_cmd,
                                        stdout=subprocess.PIPE,
                                        stdin=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        shell=True)
            res_upload = p_upload.communicate(input=b'y')[0]
            self.log.info(f"\n{res_upload.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.PERMISSION_DENIED), res_upload.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_8_contributor_upload')

    def test_core_09_upload_file_with_source(self):
        self.log.info(f"{'9 upload file to core with source file to create lineage'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user} ./{lineage_sample_file} -t tag-1 -t tag2 " \
               f"{self.cmd_option} -s {self.login_user}/{lineage_target_file} --pipeline {self.pipeline}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res.decode()}\n")
            lineage_res = self.get_lineage(f'{self.login_user}/{lineage_sample_file}')
            start_entity = lineage_res.get('start')
            mid_entity = lineage_res.get('mid')
            end_entity = lineage_res.get('end')
            start_entity_id = lineage_res.get('start_id')
            mid_entity_id = lineage_res.get('mid_id')
            end_entity_id = lineage_res.get('end_id')

            start_file_result = self.get_file_info(f'{self.login_user}/{lineage_sample_file}')
            self.log.info(f"Start file result: {start_file_result}")
            start_file_geid = start_file_result[0].get('global_entity_id')

            end_file_result = self.get_file_info(f'{self.login_user}/{lineage_target_file}')
            self.log.info(f"End file result: {end_file_result}")
            end_file_geid = end_file_result[0].get('global_entity_id')

            self.log.info(f"COMPARING target: {start_entity} VS {start_file_geid}")
            self.assertEqual(start_entity, start_file_geid)
            self.log.info(f"COMPARING pipeline: '{project_code}:{self.pipeline}' IN {mid_entity}")
            self.assertIn(f"{project_code}:{self.pipeline}", mid_entity)
            self.log.info(f"COMPARING output: {end_entity} VS {end_file_geid}")
            self.assertEqual(end_entity, end_file_geid)

            relations = lineage_res.get('relation')
            for i in range(len(relations)):
                relations[i].pop('relationshipId')
            expected_relation = [{'fromEntityId': mid_entity_id,
                                  'toEntityId': start_entity_id},
                                 {'fromEntityId': end_entity_id,
                                  'toEntityId': mid_entity_id}]
            self.log.info(f"COMPARING relations: \n"
                          f"{expected_relation} \n"
                          f"VS\n"
                          f"{relations}")
            for r in expected_relation:
                self.log.info(f"Check expected relation: {r} IN {relations}")
                self.assertIn(r, relations)
            self.file_list.append(lineage_sample_file)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_9_upload_file_with_source')

    def test_core_10_refuse_tou(self):
        self.log.info('10 refuse tou'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user} {folder_name} {self.cmd_option}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res_out = p.communicate(input=b'n')[0]
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            self.log.info("CHECK TOU IN OUTPUT")
            self.log.info("CHECK UPLOAD CANCELLED")
            self.assertIn('Aborted!', res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_10_refuse_tou')

    def test_core_11_upload_folder(self):
        self.log.info('11 upload folder'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user} {folder_name} {self.cmd_option}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res_out = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res_out.decode()}\n")
            for f1 in layer1_files:
                self.log.info(f"CHECK File {f1} uploaded")
                self.assertIn(f1, res_out.decode())
            for f2 in layer2_files:
                self.log.info(f"CHECK File {f2} uploaded")
                self.assertIn(f2, res_out.decode())
            self.assertIn('All files uploaded successfully.', res_out.decode())
            self.log.info("COMPARING FINISHED")
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_11_upload_folder')

    def test_core_12_upload_file_to_existing_folder(self):
        self.log.info(f"{'12 upload_file_to_existing_folder'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user}/{self.core_folder}/core1/core2 ./{lineage_target_file} -t tag-1 -t tag2 " \
               f"{self.cmd_option}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res.decode()}\n")
            self.assertIn(b"All files uploaded successfully.", res)
            self.file_list.append(lineage_target_file)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_12_upload_file_to_existing_folder')

    def test_core_13_upload_file_to_folder_with_source(self):
        self.log.info(f"{'13 upload file to core folder with source file to create lineage'.center(self.line_width, '=')}")
        lineage_target_path = f"{self.core_folder}/core1/core2/{lineage_target_file}"
        lineage_sample_path = f"{self.core_folder}/core1/{lineage_sample_file}"
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user}/{self.core_folder}/core1 ./{lineage_sample_file} -t tag-1 -t tag2 " \
               f"{self.cmd_option} -s {self.login_user}/{lineage_target_path} --pipeline {self.pipeline}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res.decode()}\n")
            lineage_params = {"direction": "INPUT",
                              "type_name": "file_data"}
            lineage_res = self.get_lineage(f'{self.login_user}/{lineage_sample_path}', lineage_params)

            start_file_result = self.get_file_info(f'{self.login_user}/{lineage_sample_path}')
            self.log.info(f"Start file result: {start_file_result}")
            start_file_geid = start_file_result[0].get('global_entity_id')

            end_file_result = self.get_file_info(f'{self.login_user}/{lineage_target_path}')
            self.log.info(f"End file result: {end_file_result}")
            end_file_geid = end_file_result[0].get('global_entity_id')

            self.log.info(f"lineage response: {lineage_res}")
            start_entity = lineage_res.get('start')
            mid_entity = lineage_res.get('mid')
            end_entity = lineage_res.get('end')
            start_entity_id = lineage_res.get('start_id')
            mid_entity_id = lineage_res.get('mid_id')
            end_entity_id = lineage_res.get('end_id')

            self.log.info(f"COMPARING target: {start_entity} VS {start_file_geid}")
            self.assertEqual(start_entity, start_file_geid)
            self.log.info(f"COMPARING pipeline: '{project_code}:{self.pipeline}' IN {mid_entity}")
            self.assertIn(f"{project_code}:{self.pipeline}", mid_entity)
            self.log.info(f"COMPARING output: {end_entity} VS {end_file_geid}")
            self.assertEqual(end_entity, end_file_geid)

            relations = lineage_res.get('relation')
            for i in range(len(relations)):
                relations[i].pop('relationshipId')
            expected_relation = [{'fromEntityId': mid_entity_id,
                                  'toEntityId': start_entity_id},
                                 {'fromEntityId': end_entity_id,
                                  'toEntityId': mid_entity_id}]
            self.log.info(f"COMPARING relations: \n"
                          f"{expected_relation} \n"
                          f"VS\n"
                          f"{relations}")
            for r in expected_relation:
                self.log.info(f"Check expected relation: {r} IN {relations}")
                self.assertIn(r, relations)
            self.file_list.append(lineage_sample_file)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_13_upload_file_to_folder_with_source')

    def test_core_14_upload_folder_to_folder(self):
        self.log.info('14 upload folder to folder'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user}/{self.core_folder} {folder_name} {self.cmd_option}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res_out = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res_out.decode()}\n")
            for f1 in layer1_files:
                self.log.info(f"CHECK File {f1} uploaded")
                self.assertIn(f1, res_out.decode())
            for f2 in layer2_files:
                self.log.info(f"CHECK File {f2} uploaded")
                self.assertIn(f2, res_out.decode())
            self.assertIn('All files uploaded successfully.', res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_14_upload_folder_to_folder')

    def test_core_15_list_folder(self):
        self.log.info('15 list folder'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} file list {project_code}/{self.login_user}/{self.core_folder}/core1 -z {AppConfig.Env.core_zone}"
        self.log.info(_cmd)
        try:
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            self.assertIn('core2', res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_15_list_folder')

    def test_core_16_download(self):
        self.log.info('16 download file'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} file sync {project_code}/{self.login_user}/{self.core_folder}/core1/{lineage_sample_file} ./tests/download_test -z {AppConfig.Env.core_zone}"
        self.log.info(_cmd)
        try:
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            self.log.info(f"CHECK DOWNLOADED FILE {f'./download_test/{lineage_sample_file}'}: {os.path.isfile(f'./tests/download_test/{lineage_sample_file}')}")
            self.assertTrue(os.path.isfile(f'./tests/download_test/{lineage_sample_file}'))
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_16_download')

    def test_core_17_collaborator_list_folder(self):
        self.log.info(f"{'17 collaborator list core folder'.center(self.line_width, '=')}")
        login_cmd = f"{self.cmd_path} user login -U {ConfigClass.project_collaborator.get('username')} " \
                    f"-P {ConfigClass.project_collaborator.get('password')}"
        self.log.info(login_cmd)
        _cmd = f"{self.cmd_path} file list {project_code}/{self.login_user} -z {self.zone}"
        self.log.info(_cmd)
        try:
            res_login = subprocess.check_output(login_cmd, shell=True)
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res_out = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res_login}\n")
            self.log.info(f"\n{res_out}\n")
            self.assertIn(self.core_folder, res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_17_list_folder')

    def test_core_18_upload_file_to_existing_folder_with_manifest(self):
        self.log.info(f"{'18 upload_file_to_existing_folder_with_manifest'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user}/{self.core_folder}/core1 ./{lineage_target_file} -t tag-1 -t tag2 " \
               f"{self.cmd_option} -a {self.manifest_template}"
        self.log.info(_cmd)
        manifest_definition = {
            "Manifest1": {
                "attr1": "a1",
                "attr2": "core manifest test",
                "attr3": "t1"
            }
        }
        with open(self.manifest_template, 'w') as outfile1:
            json.dump(manifest_definition, outfile1, indent=4, sort_keys=False)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res.decode()}\n")
            self.assertIn(b"All files uploaded successfully.", res)
            self.assertIn(b'Attribute attached', res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_18_upload_file_to_existing_folder_with_manifest')

    def test_core_19_batch_download_by_path(self):
        self.log.info('19 batch_download_by_path'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} file sync {project_code}/{self.login_user}/{self.core_folder}/core1/{lineage_sample_file} \
                 {project_code}/{self.login_user}/{self.core_folder}/core1/{lineage_target_file} ./tests/download_test --zip -z {AppConfig.Env.core_zone}"
        self.log.info(_cmd)
        try:
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            downloaded_zip = []
            self.log.info(f"Work dir: {os.getcwd()}")
            self.log.info(f"List dir: {os.listdir('./tests')}")
            for i in os.listdir('./tests/download_test'):
                self.log.info(f'check file: {i}')
                filename, ext = os.path.splitext(i)
                self.log.info(f"Find file: {filename}.{ext}")
                if ext == '.zip':
                    self.assertTrue(i.startswith('cli_'))
                    downloaded_zip.append(i)
            self.log.info(f"Found downloaded zip file: {downloaded_zip}")
            self.assertTrue(len(downloaded_zip) == 1)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_19_batch_download_by_path')

    def test_core_20_download_file_by_geid(self):
        self.log.info('20 download_file_by_geid'.center(self.line_width, '='))
        file1_info = self.get_file_info(f"{self.login_user}/{self.core_folder}/core1/{lineage_sample_file}")
        file2_info = self.get_file_info(f"{self.login_user}/{self.core_folder}/core1/{lineage_target_file}")
        self.log.info(f"Get file1 info: {file1_info}")
        self.log.info(f"Get file2 info: {file1_info}")
        file1_geid = file1_info[0].get('global_entity_id')
        file2_geid = file2_info[0].get('global_entity_id')
        _cmd = f"{self.cmd_path} file sync {file1_geid} {file2_geid} ./tests/download_test -i -z {AppConfig.Env.core_zone}"
        self.log.info(_cmd)
        try:
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode()}\n")
            downloaded_file = []
            self.log.info(f"Work dir: {os.getcwd()}")
            self.log.info(f"List dir: {os.listdir('./tests')}")
            for i in os.listdir('./tests/download_test'):
                self.log.info(f'check file: {i}')
                downloaded_file.append(i)
            self.log.info(f"Comparing: {lineage_sample_file} IN {downloaded_file}")
            self.assertIn(lineage_sample_file, downloaded_file)
            self.log.info(f"Comparing: {lineage_target_file} IN {downloaded_file}")
            self.assertIn(lineage_target_file, downloaded_file)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_20_download_file_by_geid')

    def test_core_21_batch_download_by_geid(self):
        self.log.info('21 batch_download_by_geid'.center(self.line_width, '='))
        file1_info = self.get_file_info(f"{self.login_user}/{self.core_folder}/core1/{lineage_sample_file}")
        file2_info = self.get_file_info(f"{self.login_user}/{self.core_folder}/core1/{lineage_target_file}")
        self.log.info(f"Get file1 info: {file1_info}")
        self.log.info(f"Get file2 info: {file1_info}")
        file1_geid = file1_info[0].get('global_entity_id')
        file2_geid = file2_info[0].get('global_entity_id')
        _cmd = f"{self.cmd_path} file sync {file1_geid} {file2_geid} ./tests/download_test -i --zip -z {AppConfig.Env.core_zone}"
        self.log.info(_cmd)
        try:
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            downloaded_zip = []
            self.log.info(f"Work dir: {os.getcwd()}")
            self.log.info(f"List dir: {os.listdir('./tests')}")
            for i in os.listdir('./tests/download_test'):
                self.log.info(f'check file: {i}')
                filename, ext = os.path.splitext(i)
                self.log.info(f"Find file: {filename}.{ext}")
                if ext == '.zip':
                    self.assertTrue(i.startswith('cli_'))
                    downloaded_zip.append(i)
            self.log.info(f"Found downloaded zip file: {downloaded_zip}")
            self.assertTrue(len(downloaded_zip) == 2)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_21_batch_download_by_geid')

    def test_core_22_upload_file_to_greenroom(self):
        self.log.info(f"{'test_core_22_upload_file_to_greenroom'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user} ./{single_file_1} -t tag-1 -t tag2"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res_out = p.communicate(input=b'y')[0]
            self.log.info(res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_22_upload_file_to_greenroom')
    
    def test_core_23_download_from_greenroom(self):
        self.log.info('test_core_23_download_from_greenroom'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} file sync {project_code}/{self.login_user}/{self.core_folder}/core1/{lineage_sample_file} ./tests/download_test"
        self.log.info(_cmd)
        try:
            res_out = subprocess.check_output(_cmd, shell=True)
            result = res_out.decode('ascii')
            self.log.info(f"\n{result}\n")
            self.log.info(f'Invalid action: download from {AppConfig.Env.green_zone} in {AppConfig.Env.core_zone} IN {result}')
            self.assertIn(f'Invalid action: download from {AppConfig.Env.green_zone} in {AppConfig.Env.core_zone}', result)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_core_23_download_from_greenroom')


if __name__ == '__main__':
    unittest.main()

