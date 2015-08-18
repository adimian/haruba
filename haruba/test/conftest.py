import pytest
import os
import json
import shutil
from unittest.mock import patch
from haruba.harubad import make_app
from haruba.database import db, Zone

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
folder_structure = [{"folder1": ['folder1-file']},
                    {"folder2": ['folder2-file1', 'folder2-file2']},
                    ["file"]]


@pytest.fixture(scope="session", autouse=True)
def prepare_srv(request):
    make_srv()
    request.addfinalizer(remove_srv)


def make_srv():
    root_path = os.path.join(ROOT_DIR, "srv")
    os.mkdir(root_path)
    for entry in folder_structure:
        make_file_or_folder(root_path, entry)


def remove_srv():
    root_path = os.path.join(ROOT_DIR, "srv")
    shutil.rmtree(root_path)


def make_file_or_folder(path, entry):
    if isinstance(entry, dict):
        folder_name = list(entry.keys())[0]
        folder_path = os.path.join(path, folder_name)
        os.mkdir(folder_path)
        make_file_or_folder(folder_path, entry[folder_name])
    elif isinstance(entry, list):
        for fn in entry:
            file_path = os.path.join(path, fn)
            with open(file_path, 'wb+') as fh:
                fh.write(b'some content')


def full_auth(*args, **kwargs):
    return {'login': 'test',
            'givenName': 'test',
            'displayName': 'test test',
            'provides': [['zone', 'read', 'test_zone'],
                         ['zone', 'write', 'test_zone'],
                         ['permissions', 'write'],
                         ['permissions', 'read']]}


def auth(*args, **kwargs):
    return {'login': 'test',
            'givenName': 'test',
            'displayName': 'test test',
            'provides': [['zone', 'read', 'test_zone'],
                         ['zone', 'write', 'test_zone']]}


def wrong_auth(*args, **kwargs):
    return {}


def is_in_data(r, key, value):
    data = json.loads(r.data.decode('utf-8'))
    assert value in data[key]


@pytest.fixture
def app():
    app = make_app()
    app.config['HARUBA_SERVE_ROOT'] = os.path.join(ROOT_DIR, "srv")
    with app.app_context():
        if not db.session.query(Zone).filter_by(name="test_zone").all():
            db.session.add(Zone("test_zone", ""))
            db.session.add(Zone("folder1_zone", "folder1"))
            db.session.commit()
    return app


@pytest.fixture
def client(app):
    client = app.test_client()
    return client


@pytest.fixture
@patch("haruba.api.request_authentication", auth)
def authenticated_client(client):
    client.post('/login', data={'login': 'me',
                                'password': 'Secret'})
    return client


@pytest.fixture
@patch("haruba.api.request_authentication", full_auth)
def admin_client(client):
    client.post('/login', data={'login': 'me',
                                'password': 'Secret'})
    return client
