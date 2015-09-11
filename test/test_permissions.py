from unittest.mock import patch
import json
import copy
from conftest import is_in_data

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


@patch("sigil_client.SigilClient.list_users", users)
@patch("sigil_client.SigilClient.provides", permissions)
def test_get_permissions(admin_client):
    ac = admin_client
    r = ac.get("/permissions")
    data = json.loads(r.data.decode('utf-8'))
    userlist = copy.deepcopy(USER_LIST)
    for user in userlist['users']:
        user['permissions'] = {'some_zone': ['read', 'write']}
    print(data)
    print(userlist)
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
