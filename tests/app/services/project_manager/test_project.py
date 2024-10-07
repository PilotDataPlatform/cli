# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from app.services.project_manager.project import SrvProjectManager


def test_list_project(requests_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    requests_mock.get(
        'http://bff_cli' + '/v1/projects',
        json={
            'code': 200,
            'error_msg': '',
            'result': [
                {
                    'name': 'PROJECT-1',
                    'code': 'project1',
                    'id': 10,
                    'geid': 'b38c26d0-1d51-44f1-9ab6-3175bd41ccc9-1620668865',
                },
                {
                    'name': 'PROJECT-2',
                    'code': 'project2',
                    'id': 20,
                    'geid': 'a6f350f4-e8ee-46eb-b346-96cfaf3853cc-1620668943',
                },
                {
                    'name': 'PROJECT-3',
                    'code': 'project3',
                    'id': 30,
                    'geid': 'e66000d6-1fd6-4386-805e-5bc8268c65b3-1620669498',
                },
            ],
        },
    )
    project_mgr = SrvProjectManager()
    project_mgr.list_projects(page=0, page_size=10, order='created_at', order_by='desc')
    out, err = capsys.readouterr()
    print_out = out.split('\n')
    assert print_out[0] == '              Project Name                            Project Code              '
    assert print_out[1] == '---------------------------------------------------------------------------'
    assert print_out[2] == '               PROJECT-1                 |               project1              '
    assert print_out[3] == '               PROJECT-2                 |               project2              '
    assert print_out[4] == '               PROJECT-3                 |               project3              '
    assert print_out[5] == ''
    assert print_out[6] == 'Page: 0, Number of projects: 3'


def test_list_project_no_project(requests_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    requests_mock.get('http://bff_cli' + '/v1/projects', json={'code': 200, 'error_msg': '', 'result': []})
    project_mgr = SrvProjectManager()
    project_mgr.list_projects(page=0, page_size=10, order='created_at', order_by='desc')
    out, err = capsys.readouterr()
    print_out = out.split('\n')
    assert print_out[0] == '              Project Name                            Project Code              '
    assert print_out[1] == '---------------------------------------------------------------------------'
    assert print_out[2] == ''
    assert print_out[3] == 'Page: 0, Number of projects: 0'


def test_list_project_desc_by_code(requests_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    requests_mock.get(
        'http://bff_cli' + '/v1/projects',
        json={
            'code': 200,
            'error_msg': '',
            'result': [
                {'name': 'project1', 'code': 'zproject', 'geid': 'fake-geid1'},
                {'name': 'project2', 'code': 'xproject', 'geid': 'fake-geid2'},
                {'name': 'project3', 'code': 'wproject', 'geid': 'fake-geid3'},
                {'name': 'project4', 'code': 'uproject', 'geid': 'fake-geid4'},
                {'name': 'project5', 'code': 'kproject', 'geid': 'fake-geid5'},
                {'name': 'project6', 'code': 'jproject', 'geid': 'fake-geid6'},
                {'name': 'project7', 'code': 'gproject', 'geid': 'fake-geid7'},
                {'name': 'project8', 'code': 'cproject', 'geid': 'fake-geid8'},
                {'name': 'project9', 'code': 'bproject', 'geid': 'fake-geid9'},
                {'name': 'project10', 'code': 'aproject', 'geid': 'fake-geid10'},
            ],
        },
    )
    project_mgr = SrvProjectManager()
    project_mgr.list_projects(page=0, page_size=10, order='code', order_by='desc')
    out, err = capsys.readouterr()
    print_out = out.split('\n')
    assert print_out[0] == '              Project Name                            Project Code              '
    assert print_out[1] == '---------------------------------------------------------------------------'
    assert print_out[2] == '                project1                 |               zproject              '
    assert print_out[3] == '                project2                 |               xproject              '
    assert print_out[4] == '                project3                 |               wproject              '
    assert print_out[5] == '                project4                 |               uproject              '
    assert print_out[6] == '                project5                 |               kproject              '
    assert print_out[7] == '                project6                 |               jproject              '
    assert print_out[8] == '                project7                 |               gproject              '
    assert print_out[9] == '                project8                 |               cproject              '
    assert print_out[10] == '                project9                 |               bproject              '
    assert print_out[11] == '               project10                 |               aproject              '
    assert print_out[12] == ''
    assert print_out[13] == 'Page: 0, Number of projects: 10'


def test_list_project_desc_by_name(requests_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    requests_mock.get(
        'http://bff_cli' + '/v1/projects',
        json={
            'code': 200,
            'error_msg': '',
            'result': [
                {'name': 'zproject1', 'code': 'project1', 'geid': 'fake-geid1'},
                {'name': 'xproject2', 'code': 'project2', 'geid': 'fake-geid2'},
                {'name': 'wproject3', 'code': 'project3', 'geid': 'fake-geid3'},
                {'name': 'uproject4', 'code': 'project4', 'geid': 'fake-geid4'},
                {'name': 'nproject5', 'code': 'project5', 'geid': 'fake-geid5'},
                {'name': 'kproject6', 'code': 'project6', 'geid': 'fake-geid6'},
                {'name': 'jproject7', 'code': 'project7', 'geid': 'fake-geid7'},
                {'name': 'gproject8', 'code': 'project8', 'geid': 'fake-geid8'},
                {'name': 'bproject9', 'code': 'project9', 'geid': 'fake-geid9'},
                {'name': 'aproject10', 'code': 'project10', 'geid': 'fake-geid10'},
            ],
        },
    )
    project_mgr = SrvProjectManager()
    project_mgr.list_projects(page=0, page_size=10, order='code', order_by='desc')
    out, err = capsys.readouterr()
    print_out = out.split('\n')
    assert print_out[0] == '              Project Name                            Project Code              '
    assert print_out[1] == '---------------------------------------------------------------------------'
    assert print_out[2] == '               zproject1                 |               project1              '
    assert print_out[3] == '               xproject2                 |               project2              '
    assert print_out[4] == '               wproject3                 |               project3              '
    assert print_out[5] == '               uproject4                 |               project4              '
    assert print_out[6] == '               nproject5                 |               project5              '
    assert print_out[7] == '               kproject6                 |               project6              '
    assert print_out[8] == '               jproject7                 |               project7              '
    assert print_out[9] == '               gproject8                 |               project8              '
    assert print_out[10] == '               bproject9                 |               project9              '
    assert print_out[11] == '               aproject10                |              project10              '
    assert print_out[12] == ''
    assert print_out[13] == 'Page: 0, Number of projects: 10'


def test_list_project_desc_by_name_with_page_size(requests_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    requests_mock.get(
        'http://bff_cli' + '/v1/projects',
        json={
            'code': 200,
            'error_msg': '',
            'result': [
                {'name': 'zproject1', 'code': 'project1', 'geid': 'fake-geid1'},
                {'name': 'xproject2', 'code': 'project2', 'geid': 'fake-geid2'},
                {'name': 'wproject3', 'code': 'project3', 'geid': 'fake-geid3'},
            ],
        },
    )
    project_mgr = SrvProjectManager()
    project_mgr.list_projects(page=0, page_size=3, order='code', order_by='desc')
    out, err = capsys.readouterr()
    print_out = out.split('\n')
    assert print_out[0] == '              Project Name                            Project Code              '
    assert print_out[1] == '---------------------------------------------------------------------------'
    assert print_out[2] == '               zproject1                 |               project1              '
    assert print_out[3] == '               xproject2                 |               project2              '
    assert print_out[4] == '               wproject3                 |               project3              '
    assert print_out[5] == ''
    assert print_out[6] == 'Page: 0, Number of projects: 3'


def test_list_project_desc_by_name_with_page_size_and_page(requests_mock, mocker, capsys):
    mocker.patch('app.services.user_authentication.token_manager.SrvTokenManager.check_valid', return_value=0)
    requests_mock.get(
        'http://bff_cli' + '/v1/projects',
        json={
            'code': 200,
            'error_msg': '',
            'result': [
                {'name': 'dproject1', 'code': 'project4', 'geid': 'fake-geid1'},
                {'name': 'cproject2', 'code': 'project5', 'geid': 'fake-geid2'},
                {'name': 'bproject3', 'code': 'project6', 'geid': 'fake-geid3'},
            ],
        },
    )
    project_mgr = SrvProjectManager()
    project_mgr.list_projects(page=1, page_size=3, order='code', order_by='desc')
    out, err = capsys.readouterr()
    print_out = out.split('\n')
    assert print_out[0] == '              Project Name                            Project Code              '
    assert print_out[1] == '---------------------------------------------------------------------------'
    assert print_out[2] == '               dproject1                 |               project4              '
    assert print_out[3] == '               cproject2                 |               project5              '
    assert print_out[4] == '               bproject3                 |               project6              '
    assert print_out[5] == ''
    assert print_out[6] == 'Page: 1, Number of projects: 3'
