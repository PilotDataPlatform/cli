# Copyright (C) 2022-2023 Indoc Research
#
# Contact Indoc Research for any questions regarding the use of this source code.

import time

import pytest

from app.configs.app_config import AppConfig
from app.configs.user_config import UserConfig
from app.models.singleton import Singleton


@pytest.fixture(autouse=True)
def reset_singletons():
    Singleton._instance = {}


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    monkeypatch.setattr(AppConfig.Connections, 'url_authn', 'http://service_auth')
    monkeypatch.setattr(AppConfig.Connections, 'url_bff', 'http://bff_cli')
    monkeypatch.setattr(UserConfig, 'username', 'test-user')
    monkeypatch.setattr(UserConfig, 'password', 'test-password')
    monkeypatch.setattr(UserConfig, 'access_token', 'test-access-token')
    monkeypatch.setattr(UserConfig, 'refresh_token', 'test-refresh-token')
    monkeypatch.setattr(UserConfig, 'hpc_token', 'test-hpc-token')


def decoded_token():
    current_time = int(time.time()) + 1000
    return {
        'exp': current_time,
        'iat': current_time,
        'auth_time': current_time - 2,
        'jti': 'f0848a19-7ddb-4170-bca4-b2ee48512ac3',
        'iss': 'http://token-auth/issuer',
        'aud': 'account',
        'sub': 'a8b728f6-c95a-4999-b98e-0ccf7492a9b4',
        'typ': 'Bearer',
        'azp': 'kong',
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
