import datetime
import json
from operator import itemgetter
import os
import shutil
from unittest.mock import patch

import pytest


ROOT_DIR = pytest.ROOT_DIR
is_in_data = pytest.is_in_data
make_srv = pytest.make_srv
remove_srv = pytest.remove_srv


class MyDatetime(datetime.datetime):
    @classmethod
    def fromtimestamp(cls, dt):
        return datetime.datetime(2016, 5, 3, 9, 53, 54)


@patch('datetime.datetime', MyDatetime)
def test_get_files(authenticated_client):
    ac = authenticated_client
    r = ac.get("/files/test_zone")
    data = json.loads(r.data.decode('utf-8'))
    data = sorted(data, key=itemgetter('name'))

    exp = [{'path': 'test_zone/file', 'uri': '/files/test_zone/file',
            'size': '12.0 B', 'name': 'file',
            'download_link': '/download/test_zone/file',
            'numeric_size': 12, 'extension': 'file',
            'modif_date': '2016-05-03 09:53:54', 'is_dir': False,
            'is_file': True},
           {'path': 'test_zone/folder1', 'uri': '/files/test_zone/folder1',
            'size': '-', 'name': 'folder1',
            'download_link': '/download/test_zone/folder1',
            'numeric_size': 0, 'extension': 'folder',
            'modif_date': '2016-05-03 09:53:54',
            'is_dir': True, 'is_file': False},
           {'path': 'test_zone/folder2', 'uri': '/files/test_zone/folder2',
            'size': '-', 'name': 'folder2',
            'download_link': '/download/test_zone/folder2', 'numeric_size': 0,
            'extension': 'folder', 'modif_date': '2016-05-03 09:53:54',
            'is_dir': True, 'is_file': False}]

    assert data == sorted(exp, key=itemgetter('name'))


def test_get_files_on_folder(authenticated_client):
    ac = authenticated_client
    r = ac.get("/files/test_zone/file")
    assert r.status_code == 400
    is_in_data(r, 'message', 'is not a folder')


def test_non_existant_path(authenticated_client):
    ac = authenticated_client
    r = ac.get("/files/test_zone/does_not_exists")
    assert r.status_code == 404


def test_create_folder(authenticated_client):
    ac = authenticated_client
    r = ac.post("/files/test_zone/new_folder")
    assert r.status_code == 200
    is_in_data(r, 'message', 'Successfully created folder')
    path = os.path.join(ROOT_DIR, "srv", "new_folder")
    os.path.exists(path)
    shutil.rmtree(path)


def test_create_existing_folder(authenticated_client):
    ac = authenticated_client
    r = ac.post("/files/test_zone/folder1")
    assert r.status_code == 400
    is_in_data(r, 'message', 'already exists')


def test_create_non_existing_folder(authenticated_client):
    ac = authenticated_client
    r = ac.post("/files/test_zone/does_not_exist/folder1")
    assert r.status_code == 400
    is_in_data(r, 'message', 'does not exist')


def test_rename(authenticated_client):
    ac = authenticated_client
    data = {'rename_to': 'ze_rename'}
    r = ac.put("/files/test_zone/folder1", data=data)
    assert r.status_code == 200
    is_in_data(r, 'message', 'Successfully renamed to')
    old = os.path.join(ROOT_DIR, "srv", "ze_rename")
    new = os.path.join(ROOT_DIR, "srv", "folder1")
    assert os.path.exists(old)
    assert not os.path.exists(new)
    os.rename(old, new)


def test_rename_exception(authenticated_client):
    ac = authenticated_client
    data = {'rename_to': 'ze_rename'}

    def rename(*args, **kwargs):
        raise Exception('os error')
    with patch('os.rename', rename):
        r = ac.put("/files/test_zone/folder1/folder1-file", data=data)
    assert r.status_code == 400
    is_in_data(r, 'message', 'Could not rename')


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
    assert r.status_code == 400
    is_in_data(r, 'message', 'does not exist')


def test_existing_delete(authenticated_client):
    ac = authenticated_client
    r = ac.delete("/files/test_zone/folder1/folder1-file")
    assert r.status_code == 200
    is_in_data(r, 'message', 'Successfully deleted')
    file_path = os.path.join(ROOT_DIR, "srv", "folder1", "folder1-file")
    with open(file_path, 'wb+') as fh:
        fh.write(b'some content')


def test_existing_delete_exception(authenticated_client):
    ac = authenticated_client

    def remove(*args, **kwargs):
        raise Exception('os error')
    with patch('os.remove', remove):
        r = ac.delete("/files/test_zone/folder1/folder1-file")
    assert r.status_code == 400
    is_in_data(r, 'message', 'Could not delete: ')


def test_existing_delete_folder_exception(authenticated_client):
    ac = authenticated_client

    def remove(*args, **kwargs):
        raise Exception('os error')
    with patch('shutil.rmtree', remove):
        r = ac.delete("/files/test_zone/folder1")
    assert r.status_code == 400
    is_in_data(r, 'message', 'Could not delete: ')


def test_existing_folder_delete(authenticated_client):
    ac = authenticated_client
    r = ac.delete("/files/test_zone/folder1")
    assert r.status_code == 200
    is_in_data(r, 'message', 'Successfully deleted')
    assert not os.path.exists(os.path.join(ROOT_DIR, "srv", "folder1"))
    remove_srv()
    make_srv()


def test_delete_specific_files(authenticated_client):
    ac = authenticated_client
    data = {'files_to_delete': ["folder2-file1"]}
    r = ac.delete("/files/test_zone/folder2", data=json.dumps(data),
                  content_type='application/json')
    assert r.status_code == 200
    is_in_data(r, 'message', 'Successfully deleted')
    assert not os.path.exists(os.path.join(ROOT_DIR, "srv",
                                           "folder2", "folder2-file1"))
    assert os.path.exists(os.path.join(ROOT_DIR, "srv",
                                       "folder2", "folder2-file2"))
    remove_srv()
    make_srv()


def test_delete_specific_files_exception(authenticated_client):
    ac = authenticated_client
    data = {'files_to_delete': ["folder2-file1"]}

    def remove(*args, **kwargs):
        raise Exception('os error')
    with patch('os.remove', remove):
        r = ac.delete("/files/test_zone/folder2", data=json.dumps(data),
                      content_type='application/json')
    assert r.status_code == 400
    is_in_data(r, 'message', 'Could not delete: ')


def test_delete_specific_files_wrong_keyword(authenticated_client):
    ac = authenticated_client
    data = {'file_to_delete': ["folder2-file1"]}
    r = ac.delete("/files/test_zone/folder2", data=json.dumps(data),
                  content_type='application/json')
    is_in_data(r, 'message', 'Wrong parameters found, aborting to prevent '
                             'unwanted deletion')
    remove_srv()
    make_srv()


def test_delete_specific_files_form_data(authenticated_client):
    ac = authenticated_client
    data = {'file_to_delete': ["folder2-file1"]}
    r = ac.delete("/files/test_zone/folder2", data=data)
    is_in_data(r, 'message', 'Detected form data, aborting to prevent '
                             'unwanted deletion')
    remove_srv()
    make_srv()
