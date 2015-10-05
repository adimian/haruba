from unittest.mock import patch
import json


def login(*args, **kwargs):
    assert args[0].username
    assert args[0].password


def totp(*args, **kwargs):
    assert kwargs.get('totp')


def no_totp(*args, **kwargs):
    raise Exception("TOTP code required")


def api_key(*args, **kwargs):
    assert args[0].api_key


def user_details(*args, **kwargs):
    return {'id': 1,
            'username': 'test',
            'firstname': 'test',
            'lastname': 'test',
            'displayname': 'test test'}


def auth(*args, **kwargs):
    return {'provides': [['zone', 'read', 'test_zone'],
                         ['zone', 'write', 'test_zone']]}


def wrong_auth(*args, **kwargs):
    return {}


@patch("sigil_client.SigilClient.login", login)
@patch("sigil_client.SigilClient.user_details", user_details)
@patch("sigil_client.SigilClient.provides", auth)
def test_login(client):
    # not yet logged in
    rv = client.get('/files/test_zone')
    assert rv.status_code == 401

    rv = client.post('/login', data={'login': 'test',
                                     'password': 'test'})
    assert rv.status_code == 200

    rv = client.get('/files/test_zone')
    assert rv.status_code == 200

    rv = client.get('/files/test')
    assert rv.status_code == 403

    rv = client.get('/login')
    assert json.loads(rv.data.decode('utf-8'))['authenticated']

    rv = client.get('/logout')
    rv = client.get('/login')
    assert not json.loads(rv.data.decode('utf-8'))['authenticated']


@patch("sigil_client.SigilClient.login", totp)
@patch("sigil_client.SigilClient.user_details", user_details)
@patch("sigil_client.SigilClient.provides", auth)
def test_login_totp(client):
    # not yet logged in
    rv = client.get('/files/test_zone')
    assert rv.status_code == 401

    rv = client.post('/login', data={'login': 'test',
                                     'password': 'test',
                                     'totp': '123456'})

    rv = client.get('/files/test_zone')
    assert rv.status_code == 200


@patch("sigil_client.SigilClient.login", no_totp)
@patch("sigil_client.SigilClient.user_details", user_details)
@patch("sigil_client.SigilClient.provides", auth)
def test_login_no_totp(client):
    # not yet logged in
    rv = client.get('/files/test_zone')
    assert rv.status_code == 401

    rv = client.post('/login', data={'login': 'test',
                                     'password': 'test',
                                     'totp': '123456'})
    assert rv.status_code == 400

    rv = client.get('/files/test_zone')
    assert rv.status_code == 401


@patch("sigil_client.SigilClient.login", api_key)
@patch("sigil_client.SigilClient.user_details", user_details)
@patch("sigil_client.SigilClient.provides", auth)
def test_login_api_key(client):
    # not yet logged in
    rv = client.get('/files/test_zone')
    assert rv.status_code == 401

    rv = client.post('/login', data={'api_key': 'test'})

    rv = client.get('/files/test_zone')
    assert rv.status_code == 200


def test_empty_login(client):
    # not yet logged in
    rv = client.get('/files/test')
    assert rv.status_code == 401

    # logging in
    rv = client.post('/login', data={})
    assert rv.status_code == 400


@patch("haruba.endpoints.login.request_authentication", wrong_auth)
def test_wrong_login(client):
    rv = client.post('/login', data={'login': 'nonexistant',
                                     'password': 'Secret'})
    assert rv.status_code == 401

    rv = client.post('/login', data={'login': 'me',
                                     'password': 'Wrong'})
    assert rv.status_code == 401
