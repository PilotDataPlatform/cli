# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import time
from typing import Any
from typing import Dict
from typing import Tuple

import jwt
import pytest

from app.configs.app_config import AppConfig
from app.configs.config import Settings
from app.configs.config import get_settings
from app.configs.user_config import UserConfig
from app.models.singleton import Singleton


@pytest.fixture(autouse=True)
def reset_singletons():
    Singleton._instances = {}


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch, mocker):
    monkeypatch.setattr(AppConfig.Connections, 'url_authn', 'http://service_auth')
    monkeypatch.setattr(AppConfig.Connections, 'url_bff', 'http://bff_cli')
    monkeypatch.setattr(AppConfig.Connections, 'url_dataset', 'http://url_dataset')
    monkeypatch.setattr(AppConfig.Connections, 'url_dataset_v2download', 'http://url_dataset_download_v2')
    monkeypatch.setattr(AppConfig.Connections, 'url_download_core', 'http://url_dataset_download_core')
    monkeypatch.setattr(AppConfig.Connections, 'url_download_greenroom', 'http://url_url_download_greenroom')
    monkeypatch.setattr(AppConfig.Connections, 'url_v2_download_pre', 'http://url_v2_download_pre/%s')
    monkeypatch.setattr(AppConfig.Connections, 'url_upload_greenroom', 'http://upload_gr')
    monkeypatch.setattr(AppConfig.Connections, 'url_upload_core', 'http://upload_core')
    monkeypatch.setattr(UserConfig, 'username', 'test-user')
    monkeypatch.setattr(UserConfig, 'password', 'test-password')
    monkeypatch.setattr(UserConfig, 'api_key', 'test-api-key')
    monkeypatch.setattr(UserConfig, 'access_token', 'test-access-token')
    monkeypatch.setattr(UserConfig, 'refresh_token', 'test-refresh-token')
    mocker.patch('app.configs.user_config.UserConfig.save')  # Do not save config when running tests


@pytest.fixture
def settings() -> Settings:
    return get_settings()


@pytest.fixture
def fake_download_hash() -> Tuple[str, Dict[str, Any]]:
    fake_file_info = {
        'file_path': 'test_file',
        'issuer': 'SERVICE DATA DOWNLOAD',
        'operator': 'admin',
        'session_id': 'admin-50708fcb-e3ae-4dad-98b5-310d79390d80',
        'job_id': '0992af70-b05c-440a-9425-4ba4f5b6d945',
        'container_code': 'test0711',
        'container_type': 'project',
        'payload': {},
        'iat': 1690576438,
        'exp': 1695760438,
    }

    download_hash = jwt.encode(fake_file_info, key='test_key', algorithm='HS256')
    return download_hash.decode('utf-8'), fake_file_info


def decoded_token():
    current_time = int(time.time()) + 1000
    return {
        'exp': current_time + 100,
        'iat': current_time,
        'auth_time': current_time - 100,
        'jti': 'f0848a19-7ddb-4170-bca4-b2ee48512ac3',
        'iss': 'http://token-auth/issuer',
        'aud': 'account',
        'sub': 'a8b728f6-c95a-4999-b98e-0ccf7492a9b4',
        'typ': 'Bearer',
        'azp': 'cli',
        'nonce': 'a3cb03d0-b00a-480d-8fd2-e06f80898cf1',
        'session_state': 'b92a3847-a485-4060-91fd-83300b09acb6',
        'acr': '1',
        'allowed-origins': ['*'],
        'realm_access': {'roles': ['offline_access', 'platform-admin', 'uma_authorization']},
        'resource_access': {'account': {'roles': ['manage-account', 'manage-account-links', 'view-profile']}},
        'scope': 'openid roles groups profile email',
        'sid': 'b92a3847-a485-4060-91fd-83300b09acb6',
        'email_verified': False,
        'name': 'test user',
        'preferred_username': 'test',
        'given_name': 'test',
        'family_name': 'user',
        'email': 'test.user@email.com',
        'group': ['sample-group'],
        'policy': ['project-admin', 'uma_authorization', 'test'],
    }


pytest_plugins = [
    'tests.fixtures.fake',
]
