import json
from haruba.test.conftest import is_in_data


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
    print(data)
    expected_data = [{'id': 1, 'name': 'test_zone', 'path': ''},
                     {'id': 2, 'name': 'folder1_zone', 'path': 'folder1'},
                     {'id': 3, 'name': 'folder2_zone', 'path': '/folder2'},
                     {'id': 4, 'name': 'folder3_zone', 'path': '/folder3'}]
    assert expected_data == data


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


def test_update_zones_no_id(admin_client):
    ac = admin_client
    command = {'zones': [{'zone': "folder2_zone_edit",
                          'path': "/folder5"}]}
    content = json.dumps(command)
    r = ac.put("/zone", data=content,
               content_type='application/json')
    r.status_code = 200
    is_in_data(r, 'message', 'must provide a zone id')


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
