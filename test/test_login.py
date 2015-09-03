from unittest.mock import patch
from conftest import auth, wrong_auth, user_details, login


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


def test_empty_login(client):
    # not yet logged in
    rv = client.get('/files/test')
    assert rv.status_code == 401

    # logging in
    rv = client.post('/login', data={})
    assert rv.status_code == 400


@patch("haruba.api.request_authentication", wrong_auth)
def test_wrong_login(client):
    rv = client.post('/login', data={'login': 'nonexistant',
                                     'password': 'Secret'})
    assert rv.status_code == 401

    rv = client.post('/login', data={'login': 'me',
                                     'password': 'Wrong'})
    assert rv.status_code == 401
