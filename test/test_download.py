import zipfile
from io import BytesIO
import pytest

is_in_data = pytest.is_in_data


def test_download_file(authenticated_client):
    ac = authenticated_client
    r = ac.get("/download/test_zone/file")
    assert r.status_code == 200
    assert r.data == b"some content"
    fn = r.headers['Content-Disposition'].replace("attachment; filename=", "")
    assert fn == "file"


def test_non_existing_download_file(authenticated_client):
    ac = authenticated_client
    r = ac.get("/download/test_zone/does_not_exist")
    assert r.status_code == 404
    is_in_data(r, "message", "Not Found:")


def test_download_folder(authenticated_client):
    ac = authenticated_client
    r = ac.get("/download/test_zone/folder2")
    assert r.status_code == 200
    files = ['folder2-file1', 'folder2-file2']
    expected_files = files
    zp = zipfile.ZipFile(BytesIO(r.data))
    il = zp.infolist()
    assert len(il) == 2
    for zf in il:
        assert zf.filename in expected_files


def test_download_multiple_file(authenticated_client):
    ac = authenticated_client
    files = ['folder2-file1', 'folder2-file2']
    data = {"filenames": files}
    r = ac.post("/download/test_zone/folder2", data=data)
    assert r.status_code == 200
    expected_files = files
    zp = zipfile.ZipFile(BytesIO(r.data))
    il = zp.infolist()
    assert len(il) == 2
    for zf in il:
        assert zf.filename in expected_files


def test_download_multiple_files_folder(authenticated_client):
    ac = authenticated_client
    files = ['folder2']
    data = {"filenames": files}
    r = ac.post("/download/test_zone", data=data)
    assert r.status_code == 200
    expected_files = ['folder2/folder2-file1', 'folder2/folder2-file2']
    zp = zipfile.ZipFile(BytesIO(r.data))
    il = zp.infolist()
    assert len(il) == 2
    for zf in il:
        assert zf.filename in expected_files


def test_download_multiple_non_existing_file(authenticated_client):
    ac = authenticated_client
    files = ['folder2-file4', 'folder2-file2']
    data = {"filenames": files}
    r = ac.post("/download/test_zone/folder2", data=data)
    assert r.status_code == 400
    is_in_data(r, "message", "Following files could not be found")
