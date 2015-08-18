from haruba.test.conftest import ROOT_DIR, is_in_data, remove_srv, make_srv
from io import BytesIO
import os
import zipfile


def prepare_uploads():
    uploads = []
    for idx, fh in enumerate([BytesIO(), BytesIO()]):
        fh.write(b"some content")
        fh.seek(0)
        uploads.append((fh, 'some_file%s' % idx))
    return uploads


def test_upload(authenticated_client):
    ac = authenticated_client
    uploads = prepare_uploads()

    r = ac.post('/upload/test_zone/folder1',
                data={'files': uploads})
    r.status_code = 200
    assert os.path.exists(os.path.join(ROOT_DIR, "srv",
                                       "folder1", "some_file0"))
    assert os.path.exists(os.path.join(ROOT_DIR, "srv",
                                       "folder1", "some_file1"))


def test_upload_to_file(authenticated_client):
    ac = authenticated_client
    uploads = prepare_uploads()

    r = ac.post('/upload/test_zone/file',
                data={'files': uploads})
    r.status_code = 400
    is_in_data(r, 'message', 'is not a folder')


def test_upload_and_unzip(authenticated_client):
    ac = authenticated_client
    upload_zip(ac, 'false')
    assert os.path.exists(os.path.join(ROOT_DIR, "srv", "folder1",
                                       "some_zip.zip"))
    remove_srv()
    make_srv()


def test_upload_and_unzip_delete(authenticated_client):
    ac = authenticated_client
    upload_zip(ac, 'true')
    assert not os.path.exists(os.path.join(ROOT_DIR, "srv", "folder1",
                                           "some_zip.zip"))
    remove_srv()
    make_srv()


def upload_zip(ac, delete_after_extract):
    zipf = BytesIO()
    uploads = ["fn1", "fn2"]
    with zipfile.ZipFile(zipf, mode='w') as zf:
        for filename in uploads:
            zf.writestr(filename, b"some content")
    zipf.seek(0)
    r = ac.post('/upload/test_zone/folder1',
                data={'files': [(zipf, "some_zip.zip")],
                      'unpack_zip': 'true',
                      'delete_zip_after_unpack': delete_after_extract})
    assert r.status_code == 200
    assert os.path.exists(os.path.join(ROOT_DIR, "srv", "folder1", "fn1"))
    assert os.path.exists(os.path.join(ROOT_DIR, "srv", "folder1", "fn2"))
