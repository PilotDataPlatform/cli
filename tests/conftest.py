# Copyright (C) 2022 Indoc Research
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import pytest
import time
from app.configs.app_config import AppConfig
from app.models.singleton import Singleton
from app.configs.user_config import UserConfig

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
            "exp": current_time,
            "iat": current_time,
            "auth_time": current_time - 2 ,
            "jti": "f0848a19-7ddb-4170-bca4-b2ee48512ac3",
            "iss": "http://token-auth/issuer",
            "aud": "account",
            "sub": "a8b728f6-c95a-4999-b98e-0ccf7492a9b4",
            "typ": "Bearer",
            "azp": "kong",
            "nonce": "a3cb03d0-b00a-480d-8fd2-e06f80898cf1",
            "session_state": "b92a3847-a485-4060-91fd-83300b09acb6",
            "acr": "1",
            "allowed-origins": [
                "*"
            ],
            "realm_access": {
                "roles": [
                    "offline_access",
                    "platform-admin",
                    "uma_authorization"
                    ]
                    },
            "resource_access": {
                "account": {
                "roles": [
                    "manage-account",
                    "manage-account-links",
                    "view-profile"
                ]
                }
            },
            "scope": "openid roles groups profile email",
            "sid": "b92a3847-a485-4060-91fd-83300b09acb6",
            "email_verified": False,
            "name": "test user",
            "preferred_username": "test",
            "given_name": "test",
            "family_name": "user",
            "email": "test.user@email.com",
            "group": [
                "sample-group"
            ],
            "policy": [
                "project-admin",
                "uma_authorization",
                "test"
            ]
        }
