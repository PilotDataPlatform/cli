# Copyright (C) 2025 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import json
import os

import click
import pytest

from app.services.file_manager.file_manifests import SrvFileManifests


def test_read_manifest_template_success():
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        # Test reading a valid manifest template
        path = 'test.json'
        expected_output = {
            'manifest_name': 'test_manifest',
            'attributes': {'attribute1': 'value1', 'attribute2': 'value2'},
        }
        with open(path, 'w') as f:
            json.dump(expected_output, f)

        result = SrvFileManifests.read_manifest_template(path)
        assert result == expected_output


def test_read_manifest_template_duplicate_line():
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        # Test reading a manifest template with duplicate lines
        path = 'test_duplicate.json'
        invalid_json = '{"manifest_name": "test_manifest", "manifest_name": "test_manifest1"}'
        with open(path, 'w') as f:
            f.write(invalid_json)

        with pytest.raises(KeyError):
            SrvFileManifests.read_manifest_template(path)


def test_manifest_listing_success_under_project(httpx_mock):
    srv_manifest = SrvFileManifests()
    # Mock the HTTP GET request
    httpx_mock.add_response(
        method='GET',
        url=f'{srv_manifest.endpoint}/manifest?project_code=test_project&manifest_name=',
        json={'result': [{'id': '123', 'manifest_name': 'test_manifest', 'attributes': {'attribute1': 'value1'}}]},
        status_code=200,
    )

    response = srv_manifest.list_manifest('test_project')
    assert response.status_code == 200
    assert response.json()['result'][0]['manifest_name'] == 'test_manifest'


def test_manifest_listing_failure(httpx_mock, capfd):
    srv_manifest = SrvFileManifests()
    # Mock the HTTP GET request
    httpx_mock.add_response(
        method='GET',
        url=f'{srv_manifest.endpoint}/manifest?project_code=test_project&manifest_name=',
        json={'error_msg': 'Manifest not found'},
        status_code=404,
    )
    try:
        _ = srv_manifest.list_manifest('test_project')
    except SystemExit:
        out, _ = capfd.readouterr()
        assert 'List Manifest Failed' in out


def test_manifest_attach_success(httpx_mock):
    srv_manifest = SrvFileManifests()
    # Mock the HTTP POST request
    httpx_mock.add_response(
        method='POST',
        url=f'{srv_manifest.endpoint}/manifest/attach',
        json={'result': {'id': '123', 'manifest_name': 'test_manifest'}},
        status_code=200,
    )

    attached = srv_manifest.attach_manifest({'manifest_name': 'test_manifest'}, 'item_id', 'zone')
    assert attached


def test_manifest_attach_failure(httpx_mock, capfd):
    srv_manifest = SrvFileManifests()
    # Mock the HTTP POST request
    httpx_mock.add_response(
        method='POST',
        url=f'{srv_manifest.endpoint}/manifest/attach',
        json={'error_msg': 'Attachment failed'},
        status_code=400,
    )

    try:
        _ = srv_manifest.attach_manifest({'manifest_name': 'test_manifest'}, 'item_id', 'zone')
    except SystemExit:
        out, _ = capfd.readouterr()
        assert 'Attribute Attach Failed' in out


def test_manifest_export_success(httpx_mock):
    srv_manifest = SrvFileManifests()
    # Mock the HTTP GET request
    httpx_mock.add_response(
        method='GET',
        url=f'{srv_manifest.endpoint}/manifest/export?project_code=test_project&name=test_manifest',
        json={'result': {'id': '123', 'manifest_name': 'test_manifest'}},
        status_code=200,
    )

    exported = srv_manifest.export_manifest('test_project', 'test_manifest')
    assert exported['manifest_name'] == 'test_manifest'


@pytest.mark.parametrize(
    'error_code, error_msg',
    [
        (403, 'Project Code not found in your project'),
        (404, 'not found in Project'),
    ],
)
def test_manifest_export_failure(httpx_mock, capfd, error_code, error_msg):
    srv_manifest = SrvFileManifests()
    # Mock the HTTP GET request
    httpx_mock.add_response(
        method='GET',
        url=f'{srv_manifest.endpoint}/manifest/export?project_code=test_project&name=test_manifest',
        json={'error_msg': 'error'},
        status_code=error_code,
    )

    try:
        _ = srv_manifest.export_manifest('test_project', 'test_manifest')
    except SystemExit:
        out, _ = capfd.readouterr()
        assert error_msg in out


def test_export_template_success():
    manifest = {
        'name': 'test_manifest',
        'project_code': 'test_project',
        'attributes': [{'name': 'attribute1', 'value': 'value1'}],
    }
    runner = click.testing.CliRunner()
    with runner.isolated_filesystem():
        srv_manifest = SrvFileManifests()
        template_file, def_file = srv_manifest.export_template(manifest['project_code'], manifest)

        # check if files are created
        assert def_file == f'{manifest["project_code"]}_{manifest["name"]}_definition.json'
        assert template_file == f'{manifest["project_code"]}_{manifest["name"]}_template.json'
        assert os.path.exists(def_file)
        assert os.path.exists(template_file)


def test_convert_import():
    srv_manifest = SrvFileManifests()
    manifest = {
        'test_manifest': {'attribute1': 'value1', 'attribute2': 'value2'},
    }
    converted = srv_manifest.convert_import(manifest, 'test_project')
    assert converted['manifest_name'] == 'test_manifest'
    assert converted['project_code'] == 'test_project'
    assert converted['attributes']['attribute1'] == 'value1'


def test_convert_export():
    srv_manifest = SrvFileManifests()
    attach_post = {
        'name': 'test_manifest',
        'project_code': 'test_project',
        'attributes': [{'name': 'attribute1', 'value': 'value1'}],
    }
    converted = srv_manifest.convert_export(attach_post)
    assert converted['test_manifest']['attribute1'] == ''
