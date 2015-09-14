import os
import zipfile

from flask import current_app, jsonify, session
from sigil_client import SigilClient

from .database import db, Zone


FILE_TYPE = 'file'
FOLDER_TYPE = 'folder'


def prep_json(*args, **kwargs):
    return args[0]


def get_sigil_client():
    client = SigilClient(current_app.config['SIGIL_API_URL'])
    client._token = session.get('sigil_token')
    return client


def success(message):
    message = {'status': 200,
               'message': message}
    resp = jsonify(message)
    resp.status_code = 200
    return resp


# ---------------- FILE OPERATIONS ----------------
# transforms pyrene_prod groups to /srv/prod/data/pyrene
# transforms pyrene_prod_backup to /srv/prod/backup/pyrene
def get_group_root(group_name):
    server_root = current_app.config['HARUBA_SERVE_ROOT']
    zone = db.session.query(Zone).filter_by(name=group_name).one()
    return os.path.join(server_root, zone.path)


def unzip(zip_dir, path, delete_after=False):
    if os.path.exists(zip_dir):
        with zipfile.ZipFile(zip_dir) as zf:
            zf.extractall(path)
        if delete_after:
            os.remove(zip_dir)
