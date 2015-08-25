import json
import os
from scandir import scandir
from datetime import datetime
from haruba.test.conftest import ROOT_DIR, is_in_data, make_srv, remove_srv
import shutil
from operator import itemgetter


def test_get_files(authenticated_client):
    ac = authenticated_client
    r = ac.get("/files/test_zone")
    data = json.loads(r.data.decode('utf-8'))
    data = sorted(data, key=itemgetter('name'))

    expected_data = []
    full_path = os.path.join(ROOT_DIR, "srv")
    for item in scandir(full_path):
        mod_date = datetime.fromtimestamp(item.stat().st_mtime)
        if item.is_file():
            extension = item.name.split(".")[-1]
        else:
            extension = 'folder'
        file_dict = {'name': item.name,
                     'is_file': item.is_file(),
                     'is_dir': item.is_dir(),
                     'size': item.stat().st_size,
                     'modif_date': mod_date.strftime('%Y-%m-%d %H:%M:%S'),
                     'extension': extension}
        expected_data.append(file_dict)
    assert data == sorted(expected_data, key=itemgetter('name'))


def test_get_files_on_folder(authenticated_client):
    ac = authenticated_client
    r = ac.get("/files/test_zone/file")
    r.status_code = 400
    is_in_data(r, 'message', 'is not a folder')


def test_non_existant_path(authenticated_client):
    ac = authenticated_client
    r = ac.get("/files/test_zone/does_not_exists")
    r.status_code = 404


def test_create_folder(authenticated_client):
    ac = authenticated_client
    r = ac.post("/files/test_zone/new_folder")
    r.status_code = 200
    is_in_data(r, 'message', 'Successfully created folder')
    path = os.path.join(ROOT_DIR, "srv", "new_folder")
    os.path.exists(path)
    shutil.rmtree(path)


def test_create_existing_folder(authenticated_client):
    ac = authenticated_client
    r = ac.post("/files/test_zone/folder1")
    r.status_code = 400
    is_in_data(r, 'message', 'already exists')


def test_create_non_existing_folder(authenticated_client):
    ac = authenticated_client
    r = ac.post("/files/test_zone/does_not_exist/folder1")
    r.status_code = 400
    is_in_data(r, 'message', 'does not exist')


def test_rename(authenticated_client):
    ac = authenticated_client
    data = {'rename_to': 'ze_rename'}
    r = ac.put("/files/test_zone/folder1", data=data)
    r.status_code = 200
    is_in_data(r, 'message', 'Successfully renamed to')
    old = os.path.join(ROOT_DIR, "srv", "ze_rename")
    new = os.path.join(ROOT_DIR, "srv", "folder1")
    assert os.path.exists(old)
    assert not os.path.exists(new)
    os.rename(old, new)


def test_empty_rename(authenticated_client):
    ac = authenticated_client
    data = {}
    r = ac.put("/files/test_zone/folder1", data=data)
    r.status_code = 400


def test_existing_rename(authenticated_client):
    ac = authenticated_client
    data = {'rename_to': 'folder2'}
    r = ac.put("/files/test_zone/folder1", data=data)
    r.status_code = 400
    is_in_data(r, 'message', 'already exists at')


def test_non_existing_rename(authenticated_client):
    ac = authenticated_client
    data = {'rename_to': 'ze_rename'}
    r = ac.put("/files/test_zone/does_not_exist/folder1", data=data)
    r.status_code = 400
    is_in_data(r, 'message', 'does not exist')


def test_non_existing_delete(authenticated_client):
    ac = authenticated_client
    r = ac.delete("/files/test_zone/folder1/folder1-file1")
    r.status_code = 400
    is_in_data(r, 'message', 'does not exist')


def test_existing_delete(authenticated_client):
    ac = authenticated_client
    r = ac.delete("/files/test_zone/folder1/folder1-file")
    r.status_code = 200
    is_in_data(r, 'message', 'Successfully deleted')
    file_path = os.path.join(ROOT_DIR, "srv", "folder1", "folder1-file")
    with open(file_path, 'wb+') as fh:
        fh.write(b'some content')


def test_existing_folder_delete(authenticated_client):
    ac = authenticated_client
    r = ac.delete("/files/test_zone/folder1")
    r.status_code = 200
    is_in_data(r, 'message', 'Successfully deleted')
    assert not os.path.exists(os.path.join(ROOT_DIR, "srv", "folder1"))
    remove_srv()
    make_srv()


def test_delete_specific_files(authenticated_client):
    ac = authenticated_client
    data = {'files_to_delete': ["folder2-file1"]}
    r = ac.delete("/files/test_zone/folder2", data=json.dumps(data),
                  content_type='application/json')
    r.status_code = 200
    is_in_data(r, 'message', 'Successfully deleted')
    assert not os.path.exists(os.path.join(ROOT_DIR, "srv",
                                           "folder2", "folder2-file1"))
    assert os.path.exists(os.path.join(ROOT_DIR, "srv",
                                       "folder2", "folder2-file2"))
    remove_srv()
    make_srv()
