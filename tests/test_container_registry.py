import unittest
import subprocess
import platform
from .logger import Logger
import random
import string
import os
project = "pilot"
class TestContainerRegistry(unittest.TestCase):
    log = Logger(name='test_container_registry.log')

    def get_bundled_app_dir(self):
        os = platform.system().lower()
        cpu = platform.processor().lower()
        if os == 'linux':
            return 'linux'
        elif os == 'darwin':
            if cpu == 'arm':
                return 'mac_arm'
            return 'mac'
    
    # generate a randomized project name to ensure no conflicts on repeated test runs
    def generate_random_project_name(self):
        random_string = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(6))
        project_name = 'pytest_' + random_string
        return project_name.lower()
    
    # requires Harbor user credentials in env
    def user_log_in(self):
        try:
            cmd = f'{self.cmd_path} user login -U {os.getenv("HARBOR_USER_USERNAME")} -P {os.getenv("HARBOR_USER_PASSWORD")}'
            res = subprocess.check_output(cmd, shell=True)
            self.log.info(f'{res.decode("ascii")}')
        except Exception as e:
            raise e

    @classmethod
    def setUpClass(cls):
        bundled_app_dir = cls.get_bundled_app_dir(cls)
        cls.cmd_path = f'app/bundled_app/{bundled_app_dir}/{project}cli'
        cls.project_name = cls.generate_random_project_name(cls)
        cls.user_log_in(cls)

    @classmethod
    def tearDownClass(cls):
        cmd = f'{cls.cmd_path} user logout -y'
        res = subprocess.check_output(cmd, shell=True)
        cls.log.info(f'{res.decode("ascii")}')

    def test_01_list_projects(self):
        self.log.info('Test case 1: List all projects')
        cmd = f'{self.cmd_path} container_registry list-projects'
        res = subprocess.check_output(cmd, shell=True)
        self.log.info(f'{res.decode("ascii")}')
        self.assertIn('Retrieved all available projects', res.decode())

    def test_02_list_repositories(self):
        self.log.info('Test case 2: List all repositories')
        cmd = f'{self.cmd_path} container_registry list-repositories'
        res = subprocess.check_output(cmd, shell=True)
        self.log.info(f'{res.decode("ascii")}')
        self.assertIn('Retrieved all available repositories', res.decode())

    # requires Harbor secret in env
    def test_03_create_project(self):
        self.log.info(f'Test case 3: Create new project named {self.project_name}')
        cmd = f'{self.cmd_path} container_registry create-project -n {self.project_name} -v public'
        res = subprocess.check_output(cmd, shell=True)
        self.log.info(f'{res.decode("ascii")}')
        self.assertIn(f'Created new project {self.project_name}', res.decode())

    def test_04_list_repositories_in_project(self):
        self.log.info(f'Test case 4: List all repositories in {self.project_name}')
        cmd = f'{self.cmd_path} container_registry list-repositories -p {self.project_name}'
        res = subprocess.check_output(cmd, shell=True)
        self.log.info(f'{res.decode("ascii")}')
        self.assertIn(f'Retrieved all available repositories in {self.project_name}', res.decode())

    # requires Harbor secret in env
    def test_05_get_user_secret(self):
        self.log.info(f'Test case 5: Get user secret')
        cmd = f'{self.cmd_path} container_registry get-secret'
        res = subprocess.check_output(cmd, shell=True)
        self.log.info(f'{res.decode("ascii")}')
        self.assertIn('Retrieved user secret', res.decode())

    # requires Harbor secret in env
    def test_06_share_project(self):
        test_user = 'dandric'
        self.log.info(f'Test case 6: Share project {self.project_name} with {test_user}')
        cmd = f'{self.cmd_path} container_registry invite-member -r guest -p {self.project_name} -u {test_user}'
        res = subprocess.check_output(cmd, shell=True)
        self.log.info(f'{res.decode("ascii")}')
        self.assertIn(f'Shared project {self.project_name} with {test_user} as guest', res.decode())
