# Copyright (C) 2022-2024 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.

import pytest

from app.configs.app_config import AppConfig
from app.services.file_manager.file_move.file_move_client import FileMoveClient
from tests.conftest import decoded_token


@pytest.mark.parametrize('root_folder', ['users', 'shared'])
def test_file_move_success(mocker, httpx_mock, root_folder):
    project_code = 'test_code'
    item_info = {'result': {'id': 'test_id', 'name': 'test_name'}}

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    mocker.patch(
        'app.services.file_manager.file_move.file_move_client.FileMoveClient.create_object_path_if_not_exist',
        return_value=[],
    )

    httpx_mock.add_response(
        url=AppConfig.Connections.url_bff + f'/v1/{project_code}/files',
        method='PATCH',
        json={'result': item_info},
    )

    file_move_client = FileMoveClient(
        'zone', project_code, f'{root_folder}/src_item_path', f'{root_folder}/dest_item_path'
    )
    res = file_move_client.move_file()
    assert res == item_info


@pytest.mark.parametrize('root_folder', ['users', 'shared'])
def test_file_move_error_with_permission_denied_403(mocker, httpx_mock, capfd, root_folder):
    project_code = 'test_code'

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    mocker.patch(
        'app.services.file_manager.file_move.file_move_client.FileMoveClient.create_object_path_if_not_exist',
        return_value=[],
    )

    httpx_mock.add_response(
        url=AppConfig.Connections.url_bff + f'/v1/{project_code}/files',
        method='PATCH',
        json={'result': {}, 'error_msg': 'error_msg'},
        status_code=403,
    )

    file_move_client = FileMoveClient(
        'zone', project_code, f'{root_folder}/src_item_path', f'{root_folder}/dest_item_path'
    )
    try:
        file_move_client.move_file()
    except SystemExit:
        out, _ = capfd.readouterr()
        assert out == f'Failed to move {root_folder}/src_item_path to {root_folder}/dest_item_path: error_msg\n'


@pytest.mark.parametrize('root_folder', ['users', 'shared'])
def test_file_move_error_with_wrong_input_422(mocker, httpx_mock, capfd, root_folder):
    project_code = 'test_code'

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    mocker.patch(
        'app.services.file_manager.file_move.file_move_client.FileMoveClient.create_object_path_if_not_exist',
        return_value=[],
    )

    httpx_mock.add_response(
        url=AppConfig.Connections.url_bff + f'/v1/{project_code}/files',
        method='PATCH',
        json={'detail': [{'loc': ['body', 'users/src_item_path'], 'msg': 'error_msg', 'type': 'value_error'}]},
        status_code=422,
    )

    file_move_client = FileMoveClient(
        'zone', project_code, f'{root_folder}/src_item_path', f'{root_folder}/dest_item_path'
    )
    try:
        file_move_client.move_file()
    except SystemExit:
        out, _ = capfd.readouterr()
        assert out == f'Failed to move {root_folder}/src_item_path to {root_folder}/dest_item_path: \nerror_msg\n'


@pytest.mark.parametrize('skip_confirmation', [True, False])
@pytest.mark.parametrize('root_folder', ['users', 'shared'])
def test_move_file_dest_parent_not_exist_success(mocker, httpx_mock, skip_confirmation, root_folder):
    project_code = 'test_code'
    item_info = {'result': {'id': 'test_id', 'name': 'test_name'}}

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    # mock duplicated item
    mocker.patch(
        'app.services.file_manager.file_move.file_move_client.check_item_duplication',
        return_value=[],
    )
    mocker.patch(
        'app.services.file_manager.file_move.file_move_client.search_item',
        return_value={'result': {'id': 'test_id', 'name': 'test_name'}},
    )
    click_mocker = mocker.patch('app.services.file_manager.file_move.file_move_client.click.confirm', return_value=None)
    httpx_mock.add_response(
        url=AppConfig.Connections.url_bff + '/v1/folders/batch',
        method='POST',
        json={'result': []},
    )

    httpx_mock.add_response(
        url=AppConfig.Connections.url_bff + f'/v1/{project_code}/files',
        method='PATCH',
        json={'result': item_info},
    )

    file_move_client = FileMoveClient(
        'zone',
        project_code,
        f'{root_folder}/src_item_path',
        f'{root_folder}/dest_item_path/test_folder/test_file',
        skip_confirm=skip_confirmation,
    )
    res = file_move_client.move_file()
    assert res == item_info
    if not skip_confirmation:
        click_mocker.assert_called_once()
    else:
        click_mocker.assert_not_called()


@pytest.mark.parametrize('skip_confirmation', [True, False])
@pytest.mark.parametrize('root_folder', ['users', 'shared'])
def test_move_file_dest_parent_lv2_not_exist_fail(mocker, httpx_mock, capfd, skip_confirmation, root_folder):
    project_code = 'test_code'

    mocker.patch(
        'app.services.user_authentication.token_manager.SrvTokenManager.decode_access_token',
        return_value=decoded_token(),
    )

    # mock duplicated item
    mocker.patch(
        'app.services.file_manager.file_move.file_move_client.check_item_duplication',
        return_value=[],
    )
    click_mocker = mocker.patch('app.services.file_manager.file_move.file_move_client.click.confirm', return_value=None)

    mocker.patch(
        'app.services.file_manager.file_move.file_move_client.search_item',
        return_value={'result': {}},
    )

    file_move_client = FileMoveClient(
        'zone',
        project_code,
        f'{root_folder}/src_item_path',
        f'{root_folder}/not_exist/test_folder/test_file',
        skip_confirm=skip_confirmation,
    )
    try:
        file_move_client.move_file()
    except SystemExit:
        out, _ = capfd.readouterr()
        assert out == f'Parent folder: {root_folder}/not_exist not exist\n'

    if not skip_confirmation:
        click_mocker.assert_called_once()
    else:
        click_mocker.assert_not_called()
