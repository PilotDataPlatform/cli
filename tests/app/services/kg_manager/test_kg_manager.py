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

from app.services.kg_manager.kg_resource import SrvKGResourceMgr


def test_import_kg(httpx_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch(
        'app.services.kg_manager.kg_resource.SrvKGResourceMgr.pre_load_data',
        return_value={'json1': 'data1', 'json2': 'data2'},
    )
    httpx_mock.add_response(
        method='POST',
        url='http://bff_cli/v1/kg/resources',
        json={
            'code': 200,
            'error_msg': '',
            'result': {
                'processing': {
                    'sample_file.json': {
                        '@context': 'https://bluebrain.github.io/nexus/contexts/metadata.json',
                        '@id': 'http://test_domain/kg/v1/resources/dataset/_/d09d9594-e495-425b-a6a6-68e230ee139e',
                        '@type': 'http://test_domain/kg/v1/vocabs/dataset/Not_Specified',
                        '_constrainedBy': 'https://bluebrain.github.io/nexus/schemas/unconstrained.json',
                        '_createdAt': '2022-03-23T13:55:51.897Z',
                        '_createdBy': 'http://test_domain/kg/v1/realms/users/test_user',
                        '_deprecated': False,
                        '_incoming': (
                            'http://test_domain/kg/v1/resources/dataset/_/'
                            'd09d9594-e495-425b-a6a6-68e230ee139e/incoming'
                        ),
                        '_outgoing': (
                            'http://test_domain/kg/v1/resources/dataset/_/'
                            'd09d9594-e495-425b-a6a6-68e230ee139e/outgoing'
                        ),
                        '_project': 'http://test_domain/kg/v1/projects/dataset',
                        '_rev': 1,
                        '_schemaProject': 'http://test_domain/kg/v1/projects/dataset',
                        '_self': 'http://test_domain/kg/v1/resources/dataset/_/d09d9594-e495-425b-a6a6-68e230ee139e',
                        '_updatedAt': '2022-03-23T13:55:51.897Z',
                        '_updatedBy': 'http://test_domain/kg/v1/realms/users/test_user',
                    }
                },
                'ignored': {},
            },
        },
    )

    kg_mgr = SrvKGResourceMgr(('fake_file.json',))
    kg_mgr.import_resource()
    out, _ = capsys.readouterr()
    assert out == 'File imported: \nsample_file.json\n'


def test_import_kg_invalid_json(mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    mocker.patch('os.path.isdir', return_value=False)
    kg_mgr = SrvKGResourceMgr(('fake_file.csv',))
    kg_mgr.import_resource()
    out, err = capsys.readouterr()
    assert out == 'Invalid action: fake_file.csv is an invalid json file\n'


def test_import_kg_folder(httpx_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    mocker.patch('os.path.isdir', return_value=True)
    mocker.patch(
        'app.services.kg_manager.kg_resource.SrvKGResourceMgr.pre_load_data',
        return_value={'json1': 'data1', 'json2': 'data2'},
    )
    httpx_mock.add_response(
        method='POST',
        url='http://bff_cli/v1/kg/resources',
        json={
            'code': 200,
            'error_msg': '',
            'result': {
                'processing': {
                    'json_test/fake_file1.json': {
                        '@context': 'https://bluebrain.github.io/nexus/contexts/metadata.json',
                        '@id': 'http://test_domain/kg/v1/resources/dataset/_/6b3d6b08-921a-4e73-9f53-93bdb77d76e1',
                        '@type': 'http://test_domain/kg/v1/vocabs/dataset/Not_Specified',
                        '_constrainedBy': 'https://bluebrain.github.io/nexus/schemas/unconstrained.json',
                        '_createdAt': '2022-03-23T18:40:23.698Z',
                        '_createdBy': 'http://test_domain/kg/v1/realms/users/test_user',
                        '_deprecated': False,
                        '_incoming': (
                            'http://test_domain/kg/v1/resources/dataset/_/'
                            '6b3d6b08-921a-4e73-9f53-93bdb77d76e1/incoming'
                        ),
                        '_outgoing': (
                            'http://test_domain/kg/v1/resources/dataset/_/'
                            '6b3d6b08-921a-4e73-9f53-93bdb77d76e1/outgoing'
                        ),
                        '_project': 'http://test_domain/kg/v1/projects/dataset',
                        '_rev': 1,
                        '_schemaProject': 'http://test_domain/kg/v1/projects/dataset',
                        '_self': 'http://test_domain/kg/v1/resources/dataset/_/6b3d6b08-921a-4e73-9f53-93bdb77d76e1',
                        '_updatedAt': '2022-03-23T18:40:23.698Z',
                        '_updatedBy': 'http://test_domain/kg/v1/realms/users/test_user',
                    },
                    'json_test/fake_file2.json': {
                        '@context': 'https://bluebrain.github.io/nexus/contexts/metadata.json',
                        '@id': 'http://test_domain/kg/v1/resources/dataset/_/b3088a27-4a44-4bf0-a952-942f9bf8a4f4',
                        '@type': 'http://test_domain/kg/v1/vocabs/dataset/Not_Specified',
                        '_constrainedBy': 'https://bluebrain.github.io/nexus/schemas/unconstrained.json',
                        '_createdAt': '2022-03-23T18:40:23.882Z',
                        '_createdBy': 'http://test_domain/kg/v1/realms/users/test_user',
                        '_deprecated': False,
                        '_incoming': (
                            'http://test_domain/kg/v1/resources/dataset/_/'
                            'b3088a27-4a44-4bf0-a952-942f9bf8a4f4/incoming'
                        ),
                        '_outgoing': (
                            'http://test_domain/kg/v1/resources/dataset/_/'
                            'b3088a27-4a44-4bf0-a952-942f9bf8a4f4/outgoing'
                        ),
                        '_project': 'http://test_domain/kg/v1/projects/dataset',
                        '_rev': 1,
                        '_schemaProject': 'http://test_domain/kg/v1/projects/dataset',
                        '_self': 'http://test_domain/kg/v1/resources/dataset/_/b3088a27-4a44-4bf0-a952-942f9bf8a4f4',
                        '_updatedAt': '2022-03-23T18:40:23.882Z',
                        '_updatedBy': 'http://test_domain/kg/v1/realms/users/test_user',
                    },
                    'json_test/fake_file3.json': {
                        '@context': 'https://bluebrain.github.io/nexus/contexts/metadata.json',
                        '@id': 'http://test_domain/kg/v1/resources/dataset/_/c45b0998-65e0-4436-a6fe-0a5b4fb1c854',
                        '@type': 'http://test_domain/kg/v1/vocabs/dataset/Not_Specified',
                        '_constrainedBy': 'https://bluebrain.github.io/nexus/schemas/unconstrained.json',
                        '_createdAt': '2022-03-23T18:40:24.071Z',
                        '_createdBy': 'http://test_domain/kg/v1/realms/users/test_user',
                        '_deprecated': False,
                        '_incoming': (
                            'http://test_domain/kg/v1/resources/dataset/_/'
                            'c45b0998-65e0-4436-a6fe-0a5b4fb1c854/incoming'
                        ),
                        '_outgoing': (
                            'http://test_domain/kg/v1/resources/dataset/_/'
                            'c45b0998-65e0-4436-a6fe-0a5b4fb1c854/outgoing'
                        ),
                        '_project': 'http://test_domain/kg/v1/projects/dataset',
                        '_rev': 1,
                        '_schemaProject': 'http://test_domain/kg/v1/projects/dataset',
                        '_self': 'http://test_domain/kg/v1/resources/dataset/_/c45b0998-65e0-4436-a6fe-0a5b4fb1c854',
                        '_updatedAt': '2022-03-23T18:40:24.071Z',
                        '_updatedBy': 'http://test_domain/kg/v1/realms/users/test_user',
                    },
                },
                'ignored': {},
            },
        },
    )

    kg_mgr = SrvKGResourceMgr(('./json_folder',))
    kg_mgr.import_resource()
    out, err = capsys.readouterr()
    assert out == (
        'File imported: \njson_test/fake_file1.json, \n' 'json_test/fake_file2.json, \njson_test/fake_file3.json\n'
    )


def test_import_kg_invalid_json_too_large(mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('os.path.getsize', return_value=1000001)
    kg_mgr = SrvKGResourceMgr(('fake_file.json',))
    kg_mgr.import_resource()
    out, err = capsys.readouterr()
    assert out == 'fake_file.json is too large\n'
