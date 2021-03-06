from unittest.mock import patch
import json
import copy
import pytest

is_in_data = pytest.is_in_data

USER_LIST = {'users': [{'username': 'alice',
                        'display_name': 'alice alice',
                        'id': 1},
                       {'username': 'bernard',
                        'display_name': 'bernard bernard',
                        'id': 2}]}

PROVIDES = {'provides': [('zone', 'read', 'some_zone'),
                         ('zone', 'write', 'some_zone')]}


def users(*args, **kwargs):
    return copy.deepcopy(USER_LIST)


def permissions(*args, **kwargs):
    return copy.deepcopy(PROVIDES)


def users_error(*args, **kwargs):
    raise Exception('some error')


def user_details(*args, **kwargs):
    return copy.deepcopy(USER_LIST['users'][0])


def api_key(*args, **kwargs):
    return 'some_api_key'


@patch("sigil_client.SigilClient.list_users", users)
@patch("sigil_client.SigilClient.provides", permissions)
def test_get_permissions(admin_client):
    ac = admin_client
    r = ac.get("/permissions")
    data = json.loads(r.data.decode('utf-8'))
    userlist = copy.deepcopy(USER_LIST)
    for user in userlist['users']:
        user['permissions'] = {'some_zone': ['read', 'write']}
    assert data == userlist


@patch("sigil_client.SigilClient.login", users_error)
def test_get_permissions_error(admin_client):
    ac = admin_client
    r = ac.get("/permissions")
    print(r.data)
    is_in_data(r, 'message', 'some error')


def permissions_return_value(*args, **kwargs):
    return "it's done, son"


def permissions_return_value_error(*args, **kwargs):
    raise Exception("it's not done, son")


data = {"permissions": [{'username': 'alice',
                         'needs': [('zone', 'read', 'some_zone'),
                                   ('zone', 'read', 'another_zone')]},
                        {'username': 'bernard',
                         'needs': [('zone', 'read', 'some_zone'),
                                   ('zone', 'read', 'another_zone')]},
                        ]}
content = json.dumps(data)


@patch("sigil_client.SigilClient.grant", permissions_return_value)
def test_grant_permissions(admin_client):
    ac = admin_client
    content = json.dumps(data)
    r = ac.post("/permissions", data=content,
                content_type='application/json')
    assert r.status_code == 200
    is_in_data(r, 'message', "Success")


@patch("sigil_client.SigilClient.grant", permissions_return_value_error)
def test_grant_permissions_error(admin_client):
    ac = admin_client
    content = json.dumps(data)
    r = ac.post("/permissions", data=content,
                content_type='application/json')
    assert r.status_code == 400
    is_in_data(r, 'message', "it's not done, son")


@patch("sigil_client.SigilClient.withdraw", permissions_return_value)
def test_withdraw_permissions(admin_client):
    ac = admin_client
    content = json.dumps(data)
    r = ac.delete("/permissions", data=content,
                  content_type='application/json')
    assert r.status_code == 200
    is_in_data(r, 'message', "Success")


def test_no_permissions(admin_client):
    ac = admin_client
    content = json.dumps({})
    r = ac.delete("/permissions", data=content,
                  content_type='application/json')
    assert r.status_code == 400
    is_in_data(r, 'message', "No permissions found")


def test_wrong_permissions(admin_client):
    ac = admin_client
    data = {"permissions": [['test', ], ]}
    content = json.dumps(data)
    r = ac.delete("/permissions", data=content,
                  content_type='application/json')
    assert r.status_code == 400
    is_in_data(r, 'message', "A need item must be a dictionary")


def test_wrong_permissions2(admin_client):
    ac = admin_client
    data = {"permissions": [{'need': []}, ]}
    content = json.dumps(data)
    r = ac.delete("/permissions", data=content,
                  content_type='application/json')
    assert r.status_code == 400
    is_in_data(r, 'message',
               "A need item must have a 'username' and 'needs' key")


def test_wrong_permissions3(admin_client):
    ac = admin_client
    data = {"permissions": [{'username': []}, ]}
    content = json.dumps(data)
    r = ac.delete("/permissions", data=content,
                  content_type='application/json')
    assert r.status_code == 400
    is_in_data(r, 'message',
               "A need item must have a 'username' and 'needs' key")


@patch("sigil_client.SigilClient.user_details", user_details)
@patch("sigil_client.SigilClient.get_api_key", api_key)
def test_get_user_details(authenticated_client):
    expected = {'provides': [{'zone': 'test_zone',
                              'access': ['read', 'write']}],
                'api_key': 'some_api_key',
                'id': 1,
                'username': 'alice',
                'display_name': 'alice alice'}
    ac = authenticated_client
    r = ac.get("/user/details")
    assert r.status_code == 200
    data = json.loads(r.data.decode('utf-8'))
    assert data == expected


def expired_token(*args, **kwargs):
    raise Exception("token has expired")


@patch("sigil_client.SigilClient.grant", expired_token)
def test_grant_permissions_expired_token(admin_client):
    ac = admin_client
    content = json.dumps(data)
    r = ac.post("/permissions", data=content,
                content_type='application/json')
    assert r.status_code == 401


def wrapped_exception(*args, **kwargs):
    raise Exception("some exception")


@patch("haruba.utils.WrappedSigilClient.wrap", wrapped_exception)
def test_grant_permissions_wrap_exception(admin_client):
    ac = admin_client
    content = json.dumps(data)
    r = ac.post("/permissions", data=content,
                content_type='application/json')
    assert r.status_code == 400
