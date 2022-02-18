import unittest
import subprocess
import os
import json
import requests
import platform
from .test_config import ConfigClass
from .logger import Logger
os.environ['env'] = "dev"
from app.configs.user_config import UserConfig
from app.utils.aggregated import get_source_file, get_folder_in_project
from app.services.output_manager.error_handler import customized_error_msg, ECustomizedError
from app.services.output_manager.message_handler import SrvOutPutHandler
from io import StringIO
import sys
import time
import datetime
import pickle

# Remember to connect VPN before test

"""
cases: greenroom, nologin, dataset, kg
"""
case_to_run = 'greenroom'

project = 'pilot'
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
dicom_project = ConfigClass.dicom_project
linux = {
    "app": "pyinstaller -F --distpath ./app/bundled_app/linux --specpath ./app/build/linux --workpath ./app/build/linux --paths=./.venv/lib/python3.8/site-packages ./app/pilotcli.py"
}

mac = {
    "app": "pyinstaller -F --distpath ./app/bundled_app/mac --specpath ./app/build/mac --workpath ./app/build/mac --paths=./.venv/lib/python3.8/site-packages ./app/pilotcli.py"
}

mac_arm = {
    "app": "pyinstaller -F --distpath ./app/bundled_app/mac_arm --specpath ./app/build/mac_arm --workpath ./app/build/mac_arm --paths=./.venv/lib/python3.8/site-packages ./app/pilotcli.py"
}

env = platform.system()
cpu = platform.processor()


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

def skipIfTrue(flag):
    def deco(f):
        def wrapper(self, *args, **kwargs):
            if getattr(self, flag):
                self.skipTest("Skipped by condition")
            else:
                f(self, *args, **kwargs)
        return wrapper
    return deco


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout

@unittest.skipUnless(case_to_run == 'greenroom' or case_to_run == 'all', 'Run specific test')
class TestCommands(unittest.TestCase):
    zone = "greenroom"
    log = Logger(name='test_greenroom.log')
    line_width = 80
    cmd_path = f"app/bundled_app/{env.lower()}/{project}cli"
    cmd_option = ''
    manifest_template = manifest_template
    login_user = ConfigClass.platform_user.get('username')


    @classmethod
    def get_file_info(cls, file_path):
        user = UserConfig()
        token = user.access_token
        try:
            cls.log.info(f"Check file in project {project_code}/{cls.zone}: {file_path}")
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
                    "operator": "***REMOVED***21",
                    "operation": "delete",
                    "project_geid": ConfigClass.project_geid,
                    "session_id": f'cli-unittest-' + stamp
                       }
            cls.log.info(f"Delete payload: {payload}")
            headers = {
                'Authorization': "Bearer " + token,
                'Session-ID': '***REMOVED***21-cli-' + stamp
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
    def setUpClass(cls):
        cls.log.info(f"{'Test setUp'.center(cls.line_width, '=')}")
        _cmd = f"{cls.cmd_path.split(' ')[0]} user logout -y"
        res = subprocess.check_output(_cmd, shell=True)
        cls.log.info(f"\n{res.decode('ascii')}\n")
        try:
            assert b'Logged out successfully. Bye!\n' == res
        except AssertionError as e:
            cls.log.warning(res)
            if b'The current login session is invalid. Please login to continue.\n' in res:
                pass
            else:
                cls.log.error(f"setup failed {str(e)}")


    @classmethod
    def tearDownClass(cls):
        cls.log.info(f"{'Test tearDown'.center(cls.line_width, '=')}")
        user = UserConfig()
        token = user.access_token
    
        deleting_list = []
        file_list=[single_file_1, single_file_2]
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
        folder_geid = folder_res.get('global_entity_id')
        deleting_list.append(folder_geid)
        try:
            cls.log.warning(f'DELETING: {deleting_list}')
            _res = cls.delete_files(deleting_list, token)
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

    def test_01_main_page_help(self):
        self.log.info(f"{'01 Test Main Page'.center(self.line_width, '=')}")
        _cmd = self.cmd_path
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(b'--help  Show this message and exit.', res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_01_main_page_help')

    def test_02_user_login(self):
        self.log.info(f"{'02 User_login'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} user login -U {ConfigClass.platform_user.get('username')} " \
               f"-P {ConfigClass.platform_user.get('password')}"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            with Capturing() as output:
                SrvOutPutHandler.login_success()
            self.log.info(f"Expected message: {output[0]}")
            self.log.info(f"Actual message: {res.decode()}")
            self.assertEqual(res.decode().replace('\n', ''), output[0])
        except Exception as e:
            self.log.error(e)
            raise Exception('test_02_user_login')

    def test_03_user_logout_invalid_input(self):
        self.log.info(f"{'03 User logout invalid input'.center(self.line_width, '=')}")
        _cmd = [self.cmd_path, "user", "logout"]
        self.log.info(' '.join(_cmd))
        self.log.info("User input: f")
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
            res_out = p.communicate(input=b'f')[0]
            self.log.info(res_out.decode())
            self.assertIn(b'Are you sure you want to logout? [y/N]: Error: invalid input', res_out)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_03_user_logout_invalid_input')

    def test_04_user_logout_cancelled(self):
        self.log.info(f"{'04 User logout cancelled'.center(self.line_width, '=')}")
        _cmd = [self.cmd_path, "user", "logout"]
        self.log.info(' '.join(_cmd))
        self.log.info("User input: n")
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
            res_out = p.communicate(input=b'n')[0]
            self.log.info(res_out.decode())
            self.assertIn(b'Are you sure you want to logout? [y/N]: Logout cancelled.\n', res_out)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_04_user_logout_cancelled')

    def test_05_user_login_invalid_password(self):
        self.log.info(f"{'05 User login invalid password'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} user login -U {ConfigClass.platform_user.get('username')} -P 12345"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.INVALID_CREDENTIALS).encode(), res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_05_user_login_invalid_password')

    def test_06_user_login_invalid_username(self):
        self.log.info(f"{'06 User login invalid username'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} user login -U InvalidUsername -P {ConfigClass.platform_user.get('password')}"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.INVALID_CREDENTIALS).encode(), res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_06_user_login_invalid_username')

    def test_07_project_list(self):
        self.log.info(f"{'07 User project list'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} project list"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(b"CLI-TEST                                              cli               ", res)
            self.assertIn("Number of projects: 3", res.decode())
            with Capturing() as output:
                SrvOutPutHandler.list_success('Project')
            self.assertIn(output[0], res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_07_project_list')

    def test_08_manifest_list(self):
        self.log.info(f"{'08 attribute list'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file attribute-list -p {project_code}"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(b'Manifest1', res)
            self.assertIn(b'Manifest2', res)
            with Capturing() as output:
                SrvOutPutHandler.all_manifest_fetched()
            self.assertIn(output[0], res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_08_manifest_list')

    def test_09_manifest_export(self):
        self.log.info(f"{'09 attribute export'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file attribute-export -p {project_code} -n Manifest1"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(b'Manifest1', res)
            self.assertIn(b'|        attr1         | multiple_choice |    a1,a2,a3,a4,a5    |  False   |', res)
            self.assertIn(b'|        attr2         |       text      |         None         |  False   |', res)
            self.assertIn(b'|        attr3         | multiple_choice |    t1,t2,t3,t4,t5    |   True   |', res)
            with Capturing() as output:
                SrvOutPutHandler.export_manifest_template(f'{project_code}_Manifest1_template.json')
            self.assertIn(output[0], res.decode())
            with Capturing() as output:
                SrvOutPutHandler.export_manifest_definition(f'{project_code}_Manifest1_definition.json')
            self.assertIn(output[0], res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_09_manifest_export')

    def test_10_manifest_list_wrong_project(self):
        self.log.info(f"{'10 attribute list wrong project code'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file attribute-list -p AbcD"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.CODE_NOT_FOUND).encode(), res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_10_manifest_list_wrong_project')

    def test_11_manifest_export_no_access_project(self):
        self.log.info(f"{'11 attribute export no access project'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file attribute-export -p testproject -n Manifest1"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.CODE_NOT_FOUND).encode(), res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_11_manifest_export_no_access_project')

    def test_12_manifest_export_non_exist_manifest(self):
        self.log.info(f"{'12 Manifest export non exist manifest'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file attribute-export -p {project_code} -n fake_manifest_n"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.MANIFEST_NOT_EXIST) % 'fake_manifest_n', res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_12_manifest_export_non_exist_manifest')

    def test_13_upload_file_with_invalid_manifest_name(self):
        self.log.info(f"{'13 upload file with invalid manifest name'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user} ./{single_file_1} -a {self.manifest_template}"
        self.log.info(_cmd)
        manifest_definition = {
            "Manifest": {
                "attr3": "t"
            }
        }
        with open(self.manifest_template, 'w') as outfile1:
            json.dump(manifest_definition, outfile1, indent=4, sort_keys=False)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.MANIFEST_NOT_EXIST) % 'Manifest', res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_13_upload_file_with_invalid_manifest_name')

    def test_14_upload_file_with_missing_reserved_attribute_in_manifest(self):
        self.log.info(f"{'14 upload file with missing reserved attribute in manifest'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user} ./{single_file_1} -a {self.manifest_template}"
        self.log.info(_cmd)
        manifest_definition = {
            "Manifest1": {
                "attr3": "t"
            }
        }
        with open(self.manifest_template, 'w') as outfile1:
            json.dump(manifest_definition, outfile1, indent=4, sort_keys=False)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode()}\n")
            self.assertIn(customized_error_msg(ECustomizedError.MISSING_REQUIRED_ATTRIBUTE) % 'attr1', res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_14_upload_file_with_missing_reserved_attribute_in_manifest')

    def test_15_upload_file_with_missing_attribute_value_in_manifest(self):
        self.log.info(f"{'15 upload file with missing attribute value in manifest'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user} ./{single_file_1} -a {self.manifest_template}"
        self.log.info(_cmd)
        manifest_definition = {
            "Manifest1": {
                "attr1": "",
                "attr3": "t"
            }
        }
        with open(self.manifest_template, 'w') as outfile1:
            json.dump(manifest_definition, outfile1, indent=4, sort_keys=False)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode()}\n")
            self.assertIn(customized_error_msg(ECustomizedError.FIELD_REQUIRED) % 'attr1', res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_15_upload_file_with_missing_attribute_value_in_manifest')

    def test_16_upload_file_with_invalid_attribute_in_manifest(self):
        self.log.info(f"{'16 upload file with invalid attribute in manifest'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user} ./{single_file_1} -a {self.manifest_template}"
        self.log.info(_cmd)
        manifest_definition = {
            "Manifest1": {
                "attr1": "a1",
                "at": "",
                "attr3": "t"
            }
        }
        with open(self.manifest_template, 'w') as outfile1:
            json.dump(manifest_definition, outfile1, indent=4, sort_keys=False)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode()}\n")
            self.assertIn(customized_error_msg(ECustomizedError.INVALID_ATTRIBUTE) % 'at', res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_16_upload_file_with_invalid_attribute_in_manifest')

    def test_17_upload_file_with_long_text_attribute_in_manifest(self):
        self.log.info(f"{'17 upload file with long text attribute in manifest'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user} ./{single_file_1} -a {self.manifest_template}"
        self.log.info(_cmd)
        manifest_definition = {
            "Manifest1": {
                "attr1": "a1",
                "attr2": "ul83vVVDsRICmDpsMhqYZMyAn3miJeR1YFeLuN87PLpFM6JGfTd080pe8T"
                         "tDuqJLLirTiXnXKbFf18vmAa2ZeC2AfeBXpMFQSef1R",
                "attr3": "t"
            }
        }
        with open(self.manifest_template, 'w') as outfile1:
            json.dump(manifest_definition, outfile1, indent=4, sort_keys=False)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode()}\n")
            self.assertIn(customized_error_msg(ECustomizedError.TEXT_TOO_LONG) % 'attr2', res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_17_upload_file_with_long_text_attribute_in_manifest')

    def test_18_upload_file_with_invalid_attribute_value_in_manifest(self):
        self.log.info(f"{'18 upload file with invalid attribute value in manifest'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user} ./{single_file_1} -a {self.manifest_template}"
        self.log.info(_cmd)
        manifest_definition = {
            "Manifest1": {
                "attr1": "a1",
                "attr2": "Test manifest text value from cli",
                "attr3": "t"
            }
        }
        with open(self.manifest_template, 'w') as outfile1:
            json.dump(manifest_definition, outfile1, indent=4, sort_keys=False)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode()}\n")
            self.assertIn(customized_error_msg(ECustomizedError.INVALID_CHOICE_FIELD) % 'attr3', res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_18_upload_file_with_invalid_attribute_value_in_manifest')

    def test_19_upload_file_with_invalid_tag_characters(self):
        self.log.info(f"{'19 upload file with invalid tag characters'.center(self.line_width, '=')}")
        invalid_char_list = ['~', '!', '@', '$', '%', '^', '_', '=',
                             '+', '[', '{', ']', '}', ':', ',', '/', '?']
        for char in invalid_char_list:
            self.log.info(char)
            _cmd = f"{self.cmd_path} file upload " \
                   f"-p {project_code}/{self.login_user} ./{single_file_1} -t " + char
            self.log.info(_cmd)
            try:
                res = subprocess.check_output(_cmd, shell=True)
                self.log.info(f"\n{res.decode()}\n")
                self.assertIn(customized_error_msg(
                    ECustomizedError.INVALID_TAG_MUST_BE_1to32_CHARACTERS_LOWER_CASE_NUMBER_OR_HYPHEN), res.decode())
            except Exception as e:
                self.log.error(e)
                raise Exception('test_19_upload_file_with_invalid_tag_characters')

    def test_20_upload_file_with_manifest_and_tag(self):
        self.log.info(f"{'20 upload file with manifest and tag'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user} ./{single_file_1} {single_file_2} " \
               f"-a {self.manifest_template} -t tag-1 -t tag2 {self.cmd_option}"
        self.log.info(_cmd)
        self.log.info(f"Option: {self.cmd_option}")
        manifest_definition = {
            "Manifest1": {
                "attr1": "a1",
                "attr2": "Test manifest text value from cli",
                "attr3": "t1"
            }
        }
        with open(self.manifest_template, 'w') as outfile1:
            json.dump(manifest_definition, outfile1, indent=4, sort_keys=False)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn('Attribute attached', res.decode())
            self.assertIn('All files uploaded successfully.', res.decode())
            self.log.info(f"validating file results {single_file_1}")
            self.validate_uploaded_file(f"{self.login_user}/{single_file_1}", manifest_definition)
            self.log.info(f"validating file results {single_file_2}")
            self.validate_uploaded_file(f"{self.login_user}/{single_file_2}", manifest_definition)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_20_upload_file_with_manifest_and_tag')

    def validate_uploaded_file(self, upload_file, manifest):

        try:
            res = self.get_file_info(upload_file)
            result = res[0]
            tags = result.get('tags')
            self.log.info(f"tags: {tags}")
            attr1 = result.get('attr_attr1')
            attr2 = result.get('attr_attr2')
            attr3 = result.get('attr_attr3')
            self.log.info(f"COMPARING: {attr1} VS {manifest.get('Manifest1').get('attr1')}")
            self.assertEqual(attr1, manifest.get('Manifest1').get('attr1'))
            self.log.info(f"COMPARING: {attr2} VS {manifest.get('Manifest1').get('attr2')}")
            self.assertEqual(attr2, manifest.get('Manifest1').get('attr2'))
            self.log.info(f"COMPARING: {attr3} VS {manifest.get('Manifest1').get('attr3')}")
            self.assertEqual(attr3, manifest.get('Manifest1').get('attr3'))
            self.log.info(f"COMPARING: {tags} VS ['tag-1', 'tag2']")
            self.assertEqual(tags, ['tag-1', 'tag2'])
        except Exception as e:
            self.log.error(f'Error validating file: {e}')

    def test_21_upload_folder_file_with_manifest_and_tag(self):
        self.log.info(f"{'21 upload folder file with manifest and tag by -f'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {dicom_project}/{self.login_user} {folder_name} -g ABC-1234 " \
               f"-t tag-1 -t tag2 {self.cmd_option}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'n')[0]
            self.log.info(f"\n{res.decode()}\n")
            self.assertIn(customized_error_msg(ECustomizedError.UNSUPPORTED_PROJECT) % ': Upload folder', res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_21_upload_folder_file_with_manifest_and_tag')

    def test_22_upload_file_already_exist(self):
        self.log.info(f"{'22 upload file already exist'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user} ./{single_file_1} " \
               f"-a {self.manifest_template} -t tag-1 -t tag2 {self.cmd_option}"
        self.log.info(_cmd)
        manifest_definition = {
            "Manifest1": {
                "attr1": "a1",
                "attr2": "Test attribute text value from cli",
                "attr3": "t1"
            }
        }
        with open(self.manifest_template, 'w') as outfile1:
            json.dump(manifest_definition, outfile1, indent=4, sort_keys=False)
        try:
            pre_res = subprocess.check_output(_cmd, shell=True)
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn('Starting upload of', res.decode())
            self.assertIn(customized_error_msg(ECustomizedError.FILE_EXIST), res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_22_upload_file_already_exist')

    def test_23_upload_file_to_no_access_project(self):
        self.log.info(f"{'23 upload file to no access project'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p may07/{self.login_user} ./{single_file_1} " \
               f"-a {self.manifest_template} -t tag-1 -t tag2 {self.cmd_option}"
        self.log.info(_cmd)
        manifest_definition = {
            "Manifest1": {
                "attr1": "a1",
                "attr2": "Test attribute text value from cli",
                "attr3": "t1"
            }
        }
        with open(self.manifest_template, 'w') as outfile1:
            json.dump(manifest_definition, outfile1, indent=4, sort_keys=False)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode()}\n")
            self.assertIn(customized_error_msg(ECustomizedError.CODE_NOT_FOUND), res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_23_upload_file_to_no_access_project')

    def test_24_upload_folder_as_zip_with_manifest_and_tag(self):
        self.log.info(f"{'24 upload folder as zip with manifest and tag'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user} {folder_name} " \
               f"-a {self.manifest_template} -t tag-1 -t tag2 {self.cmd_option} --zip"
        self.log.info(_cmd)
        manifest_definition = {
            "Manifest1": {
                "attr1": "a1",
                "attr2": "Test attribute text value from cli",
                "attr3": "t1"
            }
        }
        user = UserConfig()
        token = user.access_token
        with open(self.manifest_template, 'w') as outfile1:
            json.dump(manifest_definition, outfile1, indent=4, sort_keys=False)
        try:
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode()}\n")
            self.assertIn('Starting upload of', res_out.decode())
            upload_file = f"{self.login_user}/{folder_name.split('/')[-2]}.zip"
            self.log.info(f'Getting zip file info: {upload_file}')
            res = self.get_file_info(upload_file)
            result = res[0]
            file_geid = result.get('global_entity_id')
            self.log.info(f"find file with geid {file_geid}")
            headers = {
                'Authorization': "Bearer " + token,
            }
            folder_zip_name = folder_name.split('/')[2]
            param = {'file_geid': file_geid,
                     'project_geid': ConfigClass.project_geid}
            content_res = requests.get(url=ConfigClass.content_url_raw,
                                       headers=headers,
                                       params=param)
            self.log.info(f"URL: {ConfigClass.content_url_raw}")
            self.log.info(f"HEADERS: {headers}")
            self.log.info(f"PARAMS: {param}")
            self.log.info(content_res)
            content_json = content_res.json()
            self.log.info(content_json)
            folder = folder_name.split('/')[-2]
            sub_folder = sub_folder_name.split('/')[-1]
            content = {'tests': {'is_dir': True,
                                 folder: {
                                     'is_dir': True,
                                     layer1_files[2]: {'filename': layer1_files[2],
                                                       'size': 1048576,
                                                       'is_dir': False},
                                     layer1_files[1]: {'filename': layer1_files[1],
                                                       'size': 1048576,
                                                       'is_dir': False},
                                     layer1_files[0]: {'filename': layer1_files[0],
                                                       'size': 1048576,
                                                       'is_dir': False},
                                     sub_folder: {
                                         'is_dir': True,
                                         layer2_files[0]: {'filename': layer2_files[0],
                                                           'size': 1048576,
                                                           'is_dir': False},
                                         layer2_files[2]: {'filename': layer2_files[2],
                                                           'size': 1048576,
                                                           'is_dir': False},
                                         layer2_files[1]: {'filename': layer2_files[1],
                                                           'size': 1048576,
                                                           'is_dir': False}
                                     }
                                 }
                                 }
                       }
            self.log.info(f"Content info: {content}")
            self.log.info("Comparing zip file content layer vs folder layer")
            self.assertEqual(content_json.get('result'), content)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_24_upload_folder_as_zip_with_manifest_and_tag')

    def test_25_upload_file_without_dcm_id(self):
        self.log.info(f"{'25 upload file without dcm id'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload -p {dicom_project}/{self.login_user} ./{single_file_1} -t tag-1 -t tag2"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode()}\n")
            self.assertIn('Starting upload of', res.decode())
            self.assertIn(customized_error_msg(ECustomizedError.INVALID_DICOM_ID), res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_25_upload_file_without_dcm_id')

    def test_26_upload_folder(self):
        self.log.info(f"{'26 upload folder'.center(self.line_width, '=')}")
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
            self.log.info(f"\n{res_out}\n")
            self.log.info(f"\n{res_out.decode()}\n")
            self.assertIn('Starting upload of', res_out.decode())
            for f1 in layer1_files:
                self.log.info(f"CHECK File {f1} uploaded")
                self.assertIn(f1, res_out.decode())
            for f2 in layer2_files:
                self.log.info(f"CHECK File {f2} uploaded")
                self.assertIn(f2, res_out.decode())
            self.assertIn('All files uploaded successfully.', res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_24_upload_folder_as_zip_with_manifest_and_tag')

    def test_27_upload_folder_to_folder(self):
        self.log.info(f"{'27 upload folder'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user}/'unittest folder1'/folder1 {folder_name} {self.cmd_option}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res_out = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res_out.decode()}\n")
            self.assertIn(f'Starting upload of: {folder_name}', res_out.decode())
            for f1 in layer1_files:
                self.log.info(f"CHECK File {f1} uploaded")
                self.assertIn(f1, res_out.decode())
            for f2 in layer2_files:
                self.log.info(f"CHECK File {f2} uploaded")
                self.assertIn(f2, res_out.decode())
            self.assertIn('All files uploaded successfully.', res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_27_upload_folder_to_folder')

    def test_28_upload_folder_to_non_exist_folder(self):
        self.log.info(f"{'28 upload folder to not exist folder'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload " \
               f"-p {project_code}/{self.login_user}/{non_exist_folder} {folder_name} {self.cmd_option}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res_out = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res_out.decode()}\n")
            self.assertIn(f'Starting upload of: {folder_name}', res_out.decode())
            for f1 in layer1_files:
                self.log.info(f"CHECK File {f1} uploaded")
                self.assertIn(f1, res_out.decode())
            for f2 in layer2_files:
                self.log.info(f"CHECK File {f2} uploaded")
                self.assertIn(f2, res_out.decode())
            self.assertIn('All files uploaded successfully.', res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_28_upload_folder_to_non_exist_folder')

    def test_29_list_folder(self):
        self.log.info(f"{'29 list folder'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file list {project_code}/{self.login_user}"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res_out = p.communicate(input=b'y')[0]
            self.log.info(f"\n{res_out}\n")
            self.assertIn(non_exist_folder, res_out.decode())
            self.assertIn("unittest folder1", res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_29_list_folder')

    def test_30_download_file(self):
        self.log.info(f"{'30 download file'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file sync {project_code}/{self.login_user}/'unittest folder1'/folder1/{folder_name.lstrip('./tests/')}{layer1_files[0]} ./tests/download_test"
        self.log.info(_cmd)
        try:
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            self.assertIn("File has been downloaded successfully and saved to: ./tests/download_test/", res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_30_download_file')

    def test_31_list_project_not_exist(self):
        self.log.info(f"{'31 list project not exist'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file list {project_code}_abc1234"
        self.log.info(_cmd)
        try:
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.CODE_NOT_FOUND), res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_31_list_project_not_exist')

    def test_32_list_folder_empty(self):
        self.log.info(f"{'32 list folder no access'.center(self.line_width, '=')}")
        login_cmd = f"{self.cmd_path} user login -U {ConfigClass.project_contributor.get('username')} " \
                    f"-P {ConfigClass.project_contributor.get('password')}"
        _cmd = f"{self.cmd_path} file list {project_code}"
        self.log.info(_cmd)
        try:
            res_out = subprocess.check_output(login_cmd, shell=True)
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            self.assertIn(" ", res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_32_list_folder_no_access')

    def test_33_download_from_folder_no_access(self):
        self.log.info(f"{'33 download file no access'.center(self.line_width, '=')}")
        login_cmd = f"{self.cmd_path} user login -U {ConfigClass.project_contributor.get('username')} " \
                    f"-P {ConfigClass.project_contributor.get('password')}"
        _cmd = f"{self.cmd_path} file sync {project_code}/{self.login_user}/'unittest folder1'/folder1/{folder_name.lstrip('./tests/')}{layer1_files[0]} ./tests/download_test"
        self.log.info(_cmd)
        self.log.info(login_cmd)
        try:
            res_out = subprocess.check_output(login_cmd, shell=True)
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.PERMISSION_DENIED), res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_33_download_file_no_access')

    def test_34_download_file_no_access(self):
        self.log.info(f"{'34 download file no access'.center(self.line_width, '=')}")
        login_cmd = f"{self.cmd_path} user login -U {ConfigClass.project_contributor.get('username')} " \
                    f"-P {ConfigClass.project_contributor.get('password')}"
        _cmd = f"{self.cmd_path} file sync {project_code}/{self.login_user}/{single_file_1} ./tests/download_test"
        self.log.info(_cmd)
        self.log.info(login_cmd)
        try:
            res_out = subprocess.check_output(login_cmd, shell=True)
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.PERMISSION_DENIED), res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_34_download_file_no_access')

    def test_35_list_folder_no_access(self):
        self.log.info(f"{'35 list folder no access'.center(self.line_width, '=')}")
        login_cmd = f"{self.cmd_path} user login -U {ConfigClass.invalid_user.get('username')} " \
                    f"-P {ConfigClass.invalid_user.get('password')}"
        _cmd = f"{self.cmd_path} file list {project_code}"
        self.log.info(_cmd)
        try:
            res_out = subprocess.check_output(login_cmd, shell=True)
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            res_out = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res_out.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.CODE_NOT_FOUND), res_out.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_35_list_folder_no_access')

    def test_36_upload_file_to_existing_folder_with_manifest(self):
        self.log.info(f"{'36 upload_file_to_existing_folder_with_manifest'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user}/'unittest folder1'/folder1 ./{lineage_target_file} -t tag-1 -t tag2 " \
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
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(b"All files uploaded successfully.", res)
            self.assertIn(b'Attribute attached', res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_36_upload_file_to_existing_folder_with_manifest')

    def test_37_download_from_core(self):
        self.log.info('37 download_from_core'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} file sync {project_code}/{self.login_user}/core-test/core1/{lineage_sample_file} ./tests/download_test -z core"
        self.log.info(_cmd)
        try:
            res_out = subprocess.check_output(_cmd, shell=True)
            result = res_out.decode('ascii')
            self.log.info(f"\n{result}\n")
            self.log.info(f"'Invalid action: download from core in greenroom' IN {result}")
            self.assertIn("Invalid action: download from core in greenroom", result)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_37_download_from_core')

    def test_38_upload_file_to_core(self):
        self.log.info(f"{'38 upload_file_to_core'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload -p {project_code}/{self.login_user}/core-test/core1/core2 ./{lineage_target_file} -t tag-1 -t tag2 -z core -m test"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            result = res.decode()
            self.log.info(f"\n{result}\n")
            self.log.info(f"'Invalid action: upload to core in greenroom' IN {result}")
            self.assertIn("Invalid action: upload to core in greenroom", result)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_38_upload_file_to_core')

@unittest.skipUnless(case_to_run == 'nologin' or case_to_run == 'all', 'Run specific test')
class TestCommandsWithoutLogin(unittest.TestCase):
    zone = "greenroom"
    log = Logger(name='test_command_nologin.log')
    line_width = 80
    cmd_path = f"app/bundled_app/{env.lower()}/{project}cli"
    cmd_option = ''
    manifest_template = manifest_template

    def setUp(self):
        try:
            self.log.info(f"{'Test setUp'.center(self.line_width, '=')}")
            _cmd = f"{self.cmd_path.split(' ')[0]} user logout -y"
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            try:
                assert b'Logged out successfully. Bye!' == res
            except AssertionError as e:
                self.log.warning(res)
        except Exception as e:
            self.log.error(str(e))
            raise e

    def test_01_user_logout_without_login(self):
        self.log.info(f"{'NO-LOGIN-01 Test user logout'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} user logout -y"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.LOGIN_SESSION_INVALID).encode(), res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_01_user_logout_without_login')

    def test_02_project_list_without_login(self):
        self.log.info(f"{'NO-LOGIN-02 Project_without_login'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} project list"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.LOGIN_SESSION_INVALID).encode(), res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_02_project_list_without_login')

    def test_03_file_manifest_list_without_login(self):
        self.log.info(f"{'NO-LOGIN-03 File_manifest_list_without_login'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file attribute-list -p {project_code}"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.LOGIN_SESSION_INVALID).encode(), res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_03_file_manifest_list_without_login')

    def test_04_file_manifest_export_without_login(self):
        self.log.info(f"{'NO-LOGIN-04 File_manifest_export_without_login'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file attribute-export -p {project_code} -n {manifest_name}"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.LOGIN_SESSION_INVALID).encode(), res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_04_file_manifest_export_without_login')

    def test_05_file_upload_without_login(self):
        self.log.info(f"{'NO-LOGIN-05 File_upload_without_login'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} file upload ./cmd_upload_test -p {project_code}"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
            self.assertIn(customized_error_msg(ECustomizedError.LOGIN_SESSION_INVALID).encode(), res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_05_file_upload_without_login')

@unittest.skipUnless(case_to_run == 'dataset' or case_to_run == 'all', 'Run specific test')
class TestCommandsDataset(unittest.TestCase):
    log = Logger(name='test_dataset.log')
    line_width = 80
    cmd_path = f"app/bundled_app/{env.lower()}/{project}cli"
    login_user = ConfigClass.dataset_user.get('username')

    @classmethod
    def setUpClass(cls):
        try:
            _cmd = f"{cls.cmd_path} user login -U {cls.login_user} " \
                   f"-P {ConfigClass.dataset_user.get('password')}"
            cls.log.info(_cmd)
            res = subprocess.check_output(_cmd, shell=True)
            cls.log.info(f"\n{res.decode('ascii')}\n")
        except Exception as e:
            raise e
    
    @classmethod
    def tearDownClass(cls):
        try:
            _cmd = f"{cls.cmd_path} user logout -y"
            cls.log.info(_cmd)
            res = subprocess.check_output(_cmd, shell=True)
            cls.log.info(f"\n{res.decode('ascii')}\n")
        except Exception as e:
            raise e

    def test_01_list_dataset(self):
        self.log.info('test_01_list_dataset'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} dataset list"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn(b"dataset2                                          aug24202102           ", res)
            self.assertIn(b"dataset-01                                         aug242021            ", res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_01_list_dataset')
    
    def test_02_list_dataset_invalid_user(self):
        self.log.info('test_02_list_dataset_invalid_user'.center(self.line_width, '='))
        login_cmd = f"{self.cmd_path} user login -U {ConfigClass.invalid_user.get('username')} " \
                   f"-P {ConfigClass.invalid_user.get('password')}"
        self.log.info(login_cmd)
        _login_res = subprocess.check_output(login_cmd, shell=True)
        self.log.info(f"\n{_login_res.decode('ascii')}\n")
        _cmd = f"{self.cmd_path} dataset list"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn(b"Number of datasets: 0", res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_02_list_dataset_invalid_user')
        finally:
            _cmd = f"{self.cmd_path} user login -U {self.login_user} " \
                   f"-P {ConfigClass.dataset_user.get('password')}"
            self.log.info(_cmd)
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")

    def test_03_show_dataset_detail(self):
        self.log.info('test_03_show_dataset_detail'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} dataset show-detail aug242021"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn(b"|        Title        |                        dataset-01                      |", res)
            self.assertIn(b"|         Code        |                        aug242021                       |", res)
            self.assertIn(b"|       Authors       |                     ***REMOVED***10, cli                      |", res)
            self.assertIn(b"|         Type        |                         GENERAL                        |", res)
            self.assertIn(b"|       Modality      |     neuroimaging, microscopy, histological approach    |", res)
            self.assertIn(b"|  Collection_method  |                   import, test, upload                 |", res)
            self.assertIn(b"|         Tags        |                     tag1, tag2, tag3                   |", res)
            self.assertIn(b"|       Versions      |                      1.0, 1.1, 1.2                     |", res)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_03_show_dataset_detail')

    def test_04_show_dataset_detail_no_access(self):
        self.log.info('test_04_show_dataset_detail_no_access'.center(self.line_width, '='))
        login_cmd = f"{self.cmd_path} user login -U {ConfigClass.invalid_user.get('username')} " \
                   f"-P {ConfigClass.invalid_user.get('password')}"
        self.log.info(login_cmd)
        _login_res = subprocess.check_output(login_cmd, shell=True)
        self.log.info(f"\n{_login_res.decode('ascii')}\n")
        _cmd = f"{self.cmd_path} dataset show-detail aug242021"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn(customized_error_msg(ECustomizedError.DATASET_PERMISSION), res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_04_show_dataset_detail_no_access')
        finally:
            _cmd = f"{self.cmd_path} user login -U {self.login_user} " \
                   f"-P {ConfigClass.dataset_user.get('password')}"
            self.log.info(_cmd)
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")

    def test_05_show_dataset_detail_not_exist(self):
        self.log.info('test_05_show_dataset_detail_not_exist'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} dataset show-detail aug24202111"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn(customized_error_msg(ECustomizedError.DATASET_NOT_EXIST), res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_05_show_dataset_detail_not_exist')

    def test_06_download_dataset_not_exist(self):
        self.log.info('test_06_download_dataset_not_exist'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} dataset download aug24202111 ./tests/download_test"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn(customized_error_msg(ECustomizedError.DATASET_NOT_EXIST), res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_06_download_dataset_not_exist')

    def test_07_download_dataset_no_access(self):
        self.log.info('test_07_download_dataset_no_access'.center(self.line_width, '='))
        login_cmd = f"{self.cmd_path} user login -U {ConfigClass.invalid_user.get('username')} " \
                   f"-P {ConfigClass.invalid_user.get('password')}"
        self.log.info(login_cmd)
        _login_res = subprocess.check_output(login_cmd, shell=True)
        self.log.info(f"\n{_login_res.decode('ascii')}\n")
        _cmd = f"{self.cmd_path} dataset download aug242021 ./tests/download_test"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn(customized_error_msg(ECustomizedError.DATASET_PERMISSION), res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_07_download_dataset_no_access')
        finally:
            _cmd = f"{self.cmd_path} user login -U {self.login_user} " \
                   f"-P {ConfigClass.dataset_user.get('password')}"
            self.log.info(_cmd)
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")

    def test_08_download_dataset_wrong_version(self):
        self.log.info('test_08_download_dataset_wrong_version'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} dataset download aug242021 -v 1.1.1 ./tests/download_test"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn("Version not available: 1.1.1", res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_08_download_dataset_wrong_version')

    def test_09_download_dataset_no_version(self):
        self.log.info('test_09_download_dataset_no_version'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} dataset download aug24202102 ./tests/download_test"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn("Preparing status: READY_FOR_DOWNLOADING", res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_09_download_dataset_no_version')

    def test_10_download_dataset_no_version_multiple_input(self):
        self.log.info('test_10_download_dataset_no_version_multiple_input'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} dataset download bids0112 aug242021 aug24202102 ./tests/download_test"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn("Preparing status: READY_FOR_DOWNLOADING", res.decode())
            self.assertIn("You do not have permission to access this dataset", res.decode())
            self.assertIn("File has been downloaded successfully and saved to", res.decode())
            _root, _folder, file = next(os.walk('./tests/download_test'))
            file_dataset = []
            for f in file:
                file_dataset.append(f.split('_')[0])
            # self.assertIn('aug242021', file_dataset)
            # self.assertIn('aug24202102', file_dataset)
            self.assertNotIn('bids0112', file_dataset)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_10_download_dataset_no_version_multiple_input')

    def test_11_download_dataset_particular_version(self):
        self.log.info('test_11_download_dataset_particular_version'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} dataset download aug242021 -v 1.1 ./tests/download_test"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn("File has been downloaded successfully", res.decode())
            file_exist = os.path.isfile('./tests/download_test/aug242021_2022-01-12 11:23:29.958652.zip')
            self.assertTrue(file_exist)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_11_download_dataset_particular_version')
    
    def test_12_download_dataset_path_invalid(self):
        self.log.info('test_12_download_dataset_path_invalid'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} dataset download aug242021 -v 1.1 ./fake"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn("'OUTPUT_PATH': Path './fake' does not exist.", res.decode())
        except Exception as e:
            self.log.error(e)
            raise Exception('test_12_download_dataset_path_invalid')

    def test_13_download_dataset_version_multiple_input(self):
        self.log.info('test_13_download_dataset_version_multiple_input'.center(self.line_width, '='))
        _cmd = f"{self.cmd_path} dataset download bids0112 aug242021 aug24202102 ./tests/download_test -v 1.1"
        self.log.info(_cmd)
        try:
            p = subprocess.Popen(_cmd,
                                 stdout=subprocess.PIPE,
                                 stdin=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 shell=True)
            res = p.communicate(input=b'y')[0]
            self.log.info(res.decode())
            self.assertIn("You do not have permission to access this dataset", res.decode())
            self.assertIn("Current dataset version: 1.1", res.decode())
            self.assertIn("Version not available: 1.1", res.decode())
            file_exist = os.path.isfile('./tests/download_test/aug242021_2022-01-12 11:23:29.958652 (1).zip')
            self.assertTrue(file_exist)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_13_download_dataset_version_multiple_input')

@unittest.skipUnless(case_to_run == 'kg' or case_to_run == 'all', 'Run specific test')
class TestCommandsKG(unittest.TestCase):
    log = Logger(name='test_kg_resource.log')
    line_width = 80
    cmd_path = f"app/bundled_app/{env.lower()}/{project}cli"
    kg_def_json = f"kg_cli_test1_{stamp}.json"
    kg_dup_json = f"kg_cli_test2_{stamp}.json"
    kg_nodefault_json = f"kg_no_default_{stamp}.json"
    kg_folder = f'./tests/json_{stamp}'
    login_user = ConfigClass.platform_user.get('username')

    class Error(Exception):
        def __init__(self, message="File creation failed"):
            super().__init__(message)

    class KGDefinitioFileCreationError(Exception):
        pass

    class KGDuplicateFileCreationError(Exception):
        pass

    class KGNoDefaultFileCreationError(Exception):
        pass

    @classmethod
    def create_kg_json(cls):
        cls.log.info(f"{'creating kg_json file'.center(cls.line_width, '=')}")
        try:
            json_definition = {
                "@id": stamp,
                "@type": "unit test",
                "key_value_pairs": {
                    "definition_file": True,
                    "file_type": "KG unit test",
                    "existing_duplicate": False
                }
            }
            cls.log.info(f"Creating file: {json_definition}")
            with open(cls.kg_def_json, 'w') as outfile:
                json.dump(json_definition, outfile, indent=4, sort_keys=False)
        except Exception as e:
            cls.log.error(f"Error creating file: {str(e)}")
            raise cls.KGDefinitioFileCreationError

    @classmethod
    def create_kg_duplicate_id_json(cls):
        cls.log.info(f"{'creating kg_json file'.center(cls.line_width, '=')}")
        try:
            json_definition = {
                "@id": stamp,
        
                "@type": "unit test",
                "key_value_pairs": {
                    "definition_file": True,
                    "file_type": "KG unit test",
                    "existing_duplicate": True
                }
            }
            cls.log.info(f"Creating file: {json_definition}")
            with open(cls.kg_dup_json, 'w') as outfile:
                json.dump(json_definition, outfile, indent=4, sort_keys=False)
        except Exception as e:
            cls.log.error(f"Error creating file: {str(e)}")
            raise cls.KGDuplicateFileCreationError
    
    @classmethod
    def create_kg_no_default_value_json(cls):
        cls.log.info(f"{'creating kg_json file'.center(cls.line_width, '=')}")
        try:
            json_definition = {
                "key_value_pairs": {
                    "definition_file": False,
                    "file_type": "KG unit test",
                    "existing_duplicate": False
                }
            }
            cls.log.info(f"Creating file: {json_definition}")
            with open(cls.kg_nodefault_json, 'w') as outfile:
                json.dump(json_definition, outfile, indent=4, sort_keys=False)
        except Exception as e:
            cls.log.error(f"Error creating file: {str(e)}")
            raise cls.KGNoDefaultFileCreationError
    
    @classmethod
    def create_json_folder(cls):
        if not os.path.exists(cls.kg_folder):
            os.system(f'mkdir {cls.kg_folder}')
        for i in range(3): 
            cls.create_kg_no_default_value_json()
            if os.path.exists(cls.kg_nodefault_json):
                cls.log.info(f'mkdir {cls.kg_folder}/folder_{i}')
                os.system(f'mkdir {cls.kg_folder}/folder_{i}')
                cls.log.info("mv {cls.kg_nodefault_json} {cls.kg_folder}/folder_{i}/json_{i}.json")
                os.system(f"mv {cls.kg_nodefault_json} {cls.kg_folder}/folder_{i}/json_{i}.json")

    @classmethod
    def setUpClass(cls):
        cls.log.info(f"{'KG Test setUp'.center(cls.line_width, '=')}")
        try:
            cls.create_json_folder()
            cls.create_kg_json()
            cls.create_kg_duplicate_id_json()
            cls.create_kg_no_default_value_json()
        except cls.KGDefinitioFileCreationError:
            raise unittest.SkipTest("Setup failed")
        except cls.KGDuplicateFileCreationError:
            os.system(f"rm {cls.kg_def_json}")
            raise unittest.SkipTest("Setup failed")
        except cls.KGNoDefaultFileCreationError:
            os.system(f"rm {cls.kg_def_json} {cls.kg_dup_json}")
            raise unittest.SkipTest("Setup failed")        


    @classmethod
    def tearDownClass(cls):
        cls.log.info(f"{'KG Test teardown'.center(cls.line_width, '=')}")
        try:
            os.system(f"rm {cls.kg_def_json} {cls.kg_dup_json} {cls.kg_nodefault_json}")
            if os.path.exists(cls.kg_folder):
                cls.log.info(f'rm -rf {cls.kg_folder}')
                os.system(f'rm -rf {cls.kg_folder}')
        except Exception as e:
            cls.log.error(f"Error tearDown in KG: {str(e)}")
            raise 
    
    def setUp(self):
        try:
            _cmd = f"{self.cmd_path} user login -U {self.login_user} " \
                   f"-P {ConfigClass.platform_user.get('password')}"
            self.log.info(_cmd)
            res = subprocess.check_output(_cmd, shell=True)
            self.log.info(f"\n{res.decode('ascii')}\n")
        except Exception as e:
            raise e

    def test_01_import_resource(self):
        self.log.info(f"{'test_01_import_resource'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} kg_resource import {self.kg_def_json}"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            result = res.decode('ascii')
            self.log.info(f"\n{result}\n")
            self.log.info(f"Resource imported successfully: {self.kg_dup_json} IN {result}")
            self.assertNotIn(f"Resource imported successfully: {self.kg_nodefault_json}", result)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_01_import_resource')

    def test_02_import_resource_with_duplicate_id(self):
        self.log.info(f"{'test_02_import_resource_with_duplicate_id'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} kg_resource import {self.kg_dup_json}"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            result = res.decode('ascii')
            self.log.info(f"\n{result}\n")
            self.log.info(f"File imported: \n{self.kg_dup_json} NOTIN {result}")
            self.assertNotIn(f"File imported: \n{self.kg_nodefault_json}", result)
            self.log.info(f"File skipped: \n{self.kg_dup_json} IN {result}")
            self.assertIn(f"File skipped: \n{self.kg_dup_json}", result)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_02_import_resource_with_duplicate_id')

    def test_03_import_resource_without_default_required_fields(self):
        self.log.info(f"{'test_03_import_resource_without_default_required_fields'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} kg_resource import {self.kg_nodefault_json}"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            result = res.decode('ascii')
            self.log.info(f"\n{result}\n")
            self.log.info(f"File imported: \n{self.kg_nodefault_json} IN {result}")
            self.assertIn(f"File imported: \n{self.kg_nodefault_json}", result)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_03_import_resource_without_default_required_fields')
    
    def test_04_import_resource_not_json(self):
        self.log.info(f"{'test_04_import_resource_not_json'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} kg_resource import ./README.md"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            result = res.decode('ascii')
            self.log.info(f"\n{result}\n")
            self.log.info(f"'Invalid action: README.md is an invalid json file' IN {result}")
            self.assertIn("Invalid action: README.md is an invalid json file", result)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_04_import_resource_not_json')

    def test_05_import_resource_file_too_large(self):
        self.log.info(f"{'test_05_import_resource_file_too_large'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} kg_resource import {single_file_1}"
        self.log.info(_cmd)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            result = res.decode('ascii')
            self.log.info(f"\n{result}\n")
            self.log.info(f"'{single_file_1} is too large' IN {result}")
            self.assertIn(f"{single_file_1} is too large", result)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_05_import_resource_file_too_large')
    
    def test_06_import_folder(self):
        self.log.info(f"{'test_06_import_folder'.center(self.line_width, '=')}")
        _cmd = f"{self.cmd_path} kg_resource import {self.kg_folder} {self.kg_folder}/folder_1/json_1.json"
        self.log.info(_cmd)
        folder = os.path.relpath(self.kg_folder)
        try:
            res = subprocess.check_output(_cmd, shell=True)
            result = res.decode('ascii')
            self.log.info(f"\n{result}\n")
            self.log.info(f"CHECK OUTPUT: 'Following files have multiple input, it will process one time: \n{folder}/folder_1/json_1.json'")
            self.assertIn(f"Following files have multiple input, it will process one time: \n{folder}/folder_1/json_1.json", result)
            self.log.info(f"CHECK OUTPUT: 'File imported: \n{folder}/folder_2/json_2.json, \n{folder}/folder_1/json_1.json, \n{folder}/folder_0/json_0.json'")
            self.assertIn(f"File imported:", result)
            self.assertIn(f"\n{folder}/folder_2/json_2.json", result)
            self.assertIn(f"\n{folder}/folder_1/json_1.json", result)
            self.assertIn(f"\n{folder}/folder_0/json_0.json", result)
        except Exception as e:
            self.log.error(e)
            raise Exception('test_06_import_folder')

if __name__ == '__main__':
    unittest.main()
