from flask import current_app, jsonify, request
import os
from datetime import datetime
from haruba.database import db, Zone
from scandir import scandir
import zipfile
import tempfile
import shutil


FILE_TYPE = 'file'
FOLDER_TYPE = 'folder'


class User(object):

    def __init__(self, login, provides):
        self.login = login
        self.roles = []
        print(provides)
        for group in provides:
            self.roles.append(group)

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.login


# ---------------- ERROR SECTION ----------------
def throw_message(status, message):
    message = {'status': status,
               'message': message}
    resp = jsonify(message)
    resp.status_code = status
    return resp


def throw_success(message):
    return throw_message(200, message)


def throw_not_found():
    return throw_message(404, 'Not Found: %s' % request.url)


def throw_error(error):
    return throw_message(400, error)


def throw_unauthorised(error):
    return throw_message(401, error)


# ---------------- FILE OPERATIONS ----------------
# transforms pyrene_prod groups to /srv/prod/data/pyrene
# transforms pyrene_prod_backup to /srv/prod/backup/pyrene
def get_group_root(group_name):
    server_root = current_app.config['HARUBA_SERVE_ROOT']
    zone = db.session.query(Zone).filter_by(name=group_name).one()
    return os.path.join(server_root, zone.path)


def assemble_directory_contents(group, path):
    group_root = get_group_root(group)
    full_path = os.path.join(group_root, path)
    if not os.path.exists(full_path):
        return throw_not_found()

    files = []
    if not os.path.isdir(full_path):
        error = "%s is not a folder" % request.url
        return throw_error(error)

    for item in scandir(full_path):
        mod_date = datetime.fromtimestamp(item.stat().st_mtime)
        file_dict = {'name': item.name,
                     'is_file': item.is_file(),
                     'is_dir': item.is_dir(),
                     'size': item.stat().st_size,
                     'modif_date': mod_date.strftime('%Y-%m-%d %H:%M:%S')}
        files.append(file_dict)
    return files


def delete_file_or_folder(file_or_folder):
    try:
        if os.path.exists(file_or_folder):
            if os.path.isfile(file_or_folder):
                os.remove(file_or_folder)
            else:
                shutil.rmtree(file_or_folder)
        else:
            return False
    except Exception:
        return False
    return True


def get_path_from_group_url(url):
    if url.startswith("/"):
        url = url[1:]
    split = url.split("/")
    group = split[0]
    path = split[1:]
    return os.path.join(get_group_root(group), *path)


def construct_available_path(filepath_from, destination_folder):
    if os.path.exists(filepath_from):
        filepath_to = os.path.join(destination_folder,
                                   os.path.basename(filepath_from))
        i = 1
        if os.path.exists(filepath_to):
            fnn = "%s(%s)" % (filepath_to, i)
            while os.path.exists(fnn):
                i += 1
                fnn = "%s(%s)" % (filepath_to, i)
            filepath_to = fnn
    return filepath_to


# ---------------- ZIP SECTION ----------------
def make_zip(path, root_folder):
    folder_name = os.path.basename(path)
    temp_folder = tempfile.mkdtemp()
    zip_file = "%s.zip" % os.path.join(temp_folder,
                                       os.path.basename(folder_name))
    zipf = zipfile.ZipFile(zip_file, 'w')
    zipdir(path, zipf, root_folder)
    zipf.close()
    return zip_file


def make_selective_zip(zip_name, base_path, files):
    temp_folder = tempfile.mkdtemp()
    zip_file = "%s.zip" % os.path.join(temp_folder, zip_name)
    zipf = zipfile.ZipFile(zip_file, 'w')
    for filepath in files:
        if os.path.isdir(filepath):
            zipdir(filepath, zipf, base_path)
        else:
            zipf.write(filepath, os.path.relpath(filepath, base_path))
    zipf.close()
    return zip_file


def zipdir(path, zipf, root_folder):
    for root, dirs, files in os.walk(path):
        for fh in files:
            file_path = os.path.join(root, fh)
            zipf.write(file_path, os.path.relpath(file_path, root_folder))


def unzip(zip_dir, path, delete_after=False):
    if os.path.exists(zip_dir):
        with zipfile.ZipFile(zip_dir) as zf:
            zf.extractall(path)
        if delete_after:
            os.remove(zip_dir)
