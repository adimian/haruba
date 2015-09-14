import json
import pytest
from unittest.mock import patch
import os
import copy

ROOT_DIR = pytest.ROOT_DIR
is_in_data = pytest.is_in_data

PROVIDES = {'provides': [('zone', 'read', 'some_zone'),
                         ('zone', 'write', 'some_zone')]}


def permissions(*args, **kwargs):
    return copy.deepcopy(PROVIDES)


def declare(*args, **kwargs):
    pass


def retract(*args, **kwargs):
    pass


def test_zone(admin_client):
    ac = admin_client
    r = ac.get("/zone")
    assert r.status_code == 200
    data = json.loads(r.data.decode('utf-8'))
    assert len(data) == 2
    expected_data = [{'id': 1, 'path': '', 'name': 'test_zone'},
                     {'id': 2, 'path': 'folder1', 'name': 'folder1_zone'}]
    assert expected_data == data


def test_empty_zone(admin_client):
    ac = admin_client
    r = ac.post("/zone")
    is_in_data(r, "message", "No zones found")


def test_wrong_input(admin_client):
    ac = admin_client
    command = {'zones': [{'zone': "folder2_zone"}]}
    content = json.dumps(command)
    r = ac.post("/zone", data=content,
                content_type='application/json')
    r.status_code = 200
    is_in_data(r, 'message', 'A zone entry needs a zone and path key.')


@patch('sigil_client.SigilApplication.declare', declare)
@patch('sigil_client.SigilApplication.retract', retract)
def test_create_zones(admin_client):
    ac = admin_client
    command = {'zones': [{'zone': "folder2_zone",
                          'path': "/folder2"},
                         {'zone': "folder3_zone",
                          'path': "/folder3"}]}
    content = json.dumps(command)
    r = ac.post("/zone", data=content,
                content_type='application/json')
    r.status_code = 200
    is_in_data(r, 'message', 'Successfully created zones')

    r = ac.get("/zone")
    assert r.status_code == 200
    data = json.loads(r.data.decode('utf-8'))
    assert len(data) == 4
    expected_data = [{'id': 1, 'name': 'test_zone', 'path': ''},
                     {'id': 2, 'name': 'folder1_zone', 'path': 'folder1'},
                     {'id': 3, 'name': 'folder2_zone', 'path': 'folder2'},
                     {'id': 4, 'name': 'folder3_zone', 'path': 'folder3'}]
    folder3 = os.path.join(ROOT_DIR, "srv", "folder3")
    assert os.path.exists(folder3)
    assert expected_data == data


@patch('sigil_client.SigilApplication.declare', declare)
@patch('sigil_client.SigilApplication.retract', retract)
def test_create_existing_zones(admin_client):
    ac = admin_client
    command = {'zones': [{'zone': "test_zone",
                          'path': "/folder2"}]}
    content = json.dumps(command)
    r = ac.post("/zone", data=content,
                content_type='application/json')
    r.status_code = 400
    is_in_data(r, 'message', 'This zone already exists')


@patch('sigil_client.SigilApplication.declare', declare)
@patch('sigil_client.SigilApplication.retract', retract)
def test_update_zones(admin_client):
    ac = admin_client
    command = {'zones': [{'id': 2,
                          'zone': "folder2_zone_edit",
                          'path': "/folder5"}]}
    content = json.dumps(command)
    r = ac.put("/zone", data=content,
               content_type='application/json')
    r.status_code = 200
    is_in_data(r, 'message', 'Successfully updated zones')


@patch('sigil_client.SigilApplication.declare', declare)
@patch('sigil_client.SigilApplication.retract', retract)
def test_update_existing_zones(admin_client):
    ac = admin_client
    command = {'zones': [{'id': 2,
                          'zone': "test_zone",
                          'path': "/folder5"}]}
    content = json.dumps(command)
    r = ac.put("/zone", data=content,
               content_type='application/json')
    r.status_code = 400
    is_in_data(r, 'message', 'This zone already exists')


@patch('sigil_client.SigilApplication.declare', declare)
@patch('sigil_client.SigilApplication.retract', retract)
def test_update_zones_no_id(admin_client):
    ac = admin_client
    command = {'zones': [{'zone': "folder2_zone_edit",
                          'path': "/folder5"}]}
    content = json.dumps(command)
    r = ac.put("/zone", data=content,
               content_type='application/json')
    r.status_code = 200
    is_in_data(r, 'message', 'must provide a zone id')


@patch('sigil_client.SigilApplication.declare', declare)
@patch('sigil_client.SigilApplication.retract', retract)
def test_update_zones_wrong_id(admin_client):
    ac = admin_client
    command = {'zones': [{'id': 999,
                          'zone': "folder2_zone_edit",
                          'path': "/folder5"}]}
    content = json.dumps(command)
    r = ac.put("/zone", data=content,
               content_type='application/json')
    r.status_code = 200
    is_in_data(r, 'message', "Zone id '999' does not exist")


@patch("sigil_client.SigilClient.provides", permissions)
def test_my_zones(authenticated_client):
    ac = authenticated_client
    r = ac.get("/myzones")
    r.status_code = 200
    data = json.loads(r.data.decode('utf-8'))
    assert data == [{'access': ['read', 'write'], 'zone': 'test_zone'}]
