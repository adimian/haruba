import pytest
import os
import json
import zipfile

ROOT_DIR = pytest.ROOT_DIR
is_in_data = pytest.is_in_data
make_srv = pytest.make_srv
remove_srv = pytest.remove_srv


def base_command(command, ac):
    content = json.dumps(command)
    r = ac.post("/command/test_zone/folder1", data=content,
                content_type='application/json')
    assert r.status_code == 200
    is_in_data(r, 'message', 'Successfully executed commands')
    old = os.path.join(ROOT_DIR, "srv", "folder2", "folder2-file1")
    new = os.path.join(ROOT_DIR, "srv", "folder1", "folder2-file1")
    return old, new


def cut_command(command, ac):
    old, new = base_command(command, ac)
    assert os.path.exists(new)
    assert not os.path.exists(old)
    remove_srv()
    make_srv()


def copy_command(command, ac):
    old, new = base_command(command, ac)
    assert os.path.exists(new)
    assert os.path.exists(old)
    remove_srv()
    make_srv()


def test_cut_command_with_to(authenticated_client):
    command = {'commands': [{'type': 'cut',
                             'from': ["/test_zone/folder2/folder2-file1"],
                             'to': "/test_zone/folder1"}]}
    cut_command(command, authenticated_client)


def test_cut_command_without_to(authenticated_client):
    command = {'commands': [{'type': 'cut',
                             'from': ["/test_zone/folder2/folder2-file1"]}]}
    cut_command(command, authenticated_client)


def test_copy_command_with_to(authenticated_client):
    command = {'commands': [{'type': 'copy',
                             'from': ["/test_zone/folder2/folder2-file1"],
                             'to': "/test_zone/folder1"}]}
    copy_command(command, authenticated_client)


def test_copy_command_without_to(authenticated_client):
    command = {'commands': [{'type': 'copy',
                             'from': ["/test_zone/folder2/folder2-file1"]}]}
    copy_command(command, authenticated_client)


def test_triple_copy_command_folder(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'type': 'copy',
                             'from': ["/test_zone/folder2"],
                             'to': "/test_zone/folder1"}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone/folder1", data=content,
                content_type='application/json')
    assert r.status_code == 200

    command = {'commands': [{'type': 'copy',
                             'from': ["/test_zone/folder2"],
                             'to': "/test_zone/folder1"}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone/folder1", data=content,
                content_type='application/json')

    assert r.status_code == 200

    command = {'commands': [{'type': 'copy',
                             'from': ["/test_zone/folder2"],
                             'to': "/test_zone/folder1"}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone/folder1", data=content,
                content_type='application/json')

    assert r.status_code == 200

    old = os.path.join(ROOT_DIR, "srv", "folder2")
    new = os.path.join(ROOT_DIR, "srv", "folder1", "folder2")
    new1 = os.path.join(ROOT_DIR, "srv", "folder1", "folder2(1)")
    new2 = os.path.join(ROOT_DIR, "srv", "folder1", "folder2(2)")
    assert os.path.exists(new)
    assert os.path.exists(old)
    assert os.path.exists(new1)
    assert os.path.exists(new2)
    remove_srv()
    make_srv()


def test_unknown_command(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'type': 'cuttt',
                             'from': ["/test_zone/folder2/folder2-file1"],
                             'to': "/test_zone/folder1"}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone/folder1", data=content,
                content_type='application/json')
    r.status_code = 400
    is_in_data(r, 'message', 'is not a valid comand')


def test_no_command(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'from': ["/test_zone/folder2/folder2-file1"],
                             'to': "/test_zone/folder1"}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone/folder1", data=content,
                content_type='application/json')
    r.status_code = 400
    is_in_data(r, 'message', 'Must provide a command type')


def test_wrong_input_string(authenticated_client):
    ac = authenticated_client
    command = {'commands': ["wrong input"]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone/folder1", data=content,
                content_type='application/json')
    r.status_code = 400
    is_in_data(r, 'message', ("Input must be a dict containing"
                              " 'type' and 'from' keys, not string"))


def test_wrong_input_list(authenticated_client):
    ac = authenticated_client
    command = {'commands': [["wrong input", ]]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone/folder1", data=content,
                content_type='application/json')
    r.status_code = 400
    is_in_data(r, 'message', ("Input must be a dict containing"
                              " 'type' and 'from' keys, not list"))


def test_wrong_to_path(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'type': 'cut',
                             'from': ["/test_zone/folder2/folder2-file1"],
                             'to': "/test_zone/does_not_exist"}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone/folder1", data=content,
                content_type='application/json')
    r.status_code = 400
    is_in_data(r, 'message', "does not exist")


def test_wrong_from_path(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'type': 'cut',
                             'from': ["/test_zone/folder2/does_not_exist"],
                             'to': "/test_zone/folder1"}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone/folder1", data=content,
                content_type='application/json')
    r.status_code = 400
    is_in_data(r, 'message', "Path does not exist")


def test_to_path_is_file(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'type': 'cut',
                             'from': ["/test_zone/folder2/folder2-file1"],
                             'to': "/test_zone/file"}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone/folder1", data=content,
                content_type='application/json')
    r.status_code = 400
    is_in_data(r, 'message', "must be a directory")


def create_zip():
    path = os.path.join(ROOT_DIR, "srv", "some_zip.zip")
    files = ["fn1", "fn2"]
    with zipfile.ZipFile(path, mode='w') as zf:
        for filename in files:
            zf.writestr(filename, b"some content")
    return path


def unzip(command, ac):
    path = create_zip()
    content = json.dumps(command)
    r = ac.post("/command/test_zone/some_zip.zip", data=content,
                content_type='application/json')
    r.status_code = 200
    fn1 = os.path.join(ROOT_DIR, "srv", "fn1")
    fn2 = os.path.join(ROOT_DIR, "srv", "fn2")
    assert os.path.exists(fn1)
    assert os.path.exists(fn2)
    os.remove(fn1)
    os.remove(fn2)
    return path


def test_unzip_delete(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'type': 'unzip',
                             'delete_zip_after_unpack': True}]}
    path = unzip(command, ac)
    assert not os.path.exists(path)


def test_unzip_not_delete(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'type': 'unzip',
                             'delete_zip_after_unpack': False}]}
    path = unzip(command, ac)
    assert os.path.exists(path)
    os.remove(path)


def test_unzip_wrong_file(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'type': 'unzip',
                             'delete_zip_after_unpack': True}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone/file", data=content,
                content_type='application/json')
    assert r.status_code == 400
    is_in_data(r, 'message', 'is not a valid zipfile')


def test_cut_command_without_from(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'type': 'cut'}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone", data=content,
                content_type='application/json')
    assert r.status_code == 400
    is_in_data(r, 'message', "To copy or cut you must provide a 'from' key")


def test_cut_to_no_read_permission_group(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'type': 'cut',
                             'from': ["/folder1_zone/folder1-file"],
                             'to': "/test_zone/folder2"}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone", data=content,
                content_type='application/json')
    assert r.status_code == 401
    is_in_data(r, 'message', 'You are not allowed to read in zone')


def test_cut_to_no_write_permission_group(authenticated_client):
    ac = authenticated_client
    command = {'commands': [{'type': 'cut',
                             'from': ["/test_zone/folder2/folder2-file1"],
                             'to': "/folder1_zone"}]}
    content = json.dumps(command)
    r = ac.post("/command/test_zone", data=content,
                content_type='application/json')
    assert r.status_code == 401
    is_in_data(r, 'message', 'You are not allowed to write in zone')













