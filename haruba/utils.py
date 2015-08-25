from flask import current_app, jsonify, request, abort, session
import os
from datetime import datetime
from haruba.database import db, Zone
from scandir import scandir
import zipfile
import tempfile
import shutil
from sigil_client import SigilClient
from collections import defaultdict


FILE_TYPE = 'file'
FOLDER_TYPE = 'folder'


class User(object):

    def __init__(self, login, provides):
        self.login = login
        self.roles = []
        self.zones = defaultdict(list)
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

    def add_zone(self, permissions):
        _, permission, zone = permissions
        self.zones[zone].append(permission)


def prep_json(*args, **kwargs):
    return args[0]


def get_sigil_client():
    client = SigilClient(current_app.config['SIGIL_API_URL'])
    client._token = session.get('sigil_token')
    return client


# ---------------- ERROR SECTION ----------------
def throw_success(message):
    message = {'status': 200,
               'message': message}
    resp = jsonify(message)
    resp.status_code = 200
    return resp


def throw_not_found():
    abort(404, 'Not Found: %s' % request.url)


def throw_error(error):
    abort(400, error)


def throw_unauthorised(error):
    abort(401, error)


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

    if not os.path.isdir(full_path):
        error = "%s is not a folder" % request.url
        return throw_error(error)

    folders = []
    files = []
    for item in scandir(full_path):
        mod_date = datetime.fromtimestamp(item.stat().st_mtime)
        file_dict = {'name': item.name,
                     'is_file': item.is_file(),
                     'is_dir': item.is_dir(),
                     'size': item.stat().st_size,
                     'modif_date': mod_date.strftime('%Y-%m-%d %H:%M:%S')}
        if item.is_dir():
            file_dict['extension'] = "folder"
            folders.append(file_dict)
        else:
            file_dict['extension'] = item.name.split(".")[-1]
            files.append(file_dict)
    return folders + files


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
    print(url)
    if url.startswith("/"):
        url = url[1:]
    split = url.split("/")
    group = split[0]
    path = split[1:]
    return os.path.join(get_group_root(group), *path)


def construct_available_path(filepath_from, destination_folder):
    print(filepath_from)
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
    throw_error("Path does not exist")


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
    for root, _, files in os.walk(path):
        for fh in files:
            file_path = os.path.join(root, fh)
            zipf.write(file_path, os.path.relpath(file_path, root_folder))


def unzip(zip_dir, path, delete_after=False):
    print(delete_after)
    if os.path.exists(zip_dir):
        with zipfile.ZipFile(zip_dir) as zf:
            zf.extractall(path)
        if delete_after:
            os.remove(zip_dir)
