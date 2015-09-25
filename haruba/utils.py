import os
import zipfile

from flask import current_app, jsonify, session, abort
from flask_login import logout_user, current_user
from sigil_client import SigilClient

from .database import db, Zone


FILE_TYPE = 'file'
FOLDER_TYPE = 'folder'


def prep_json(*args, **kwargs):
    return args[0]


def get_sigil_client():
    return WrappedSigilClient()


class WrappedSigilClient(object):
    def __init__(self, *args, **kwargs):
        self.client = SigilClient(current_app.config['SIGIL_API_URL'],
                                  *args, **kwargs)
        self.client._token = session.get('sigil_token')

    def __getattr__(self, name):
        try:
            attr = getattr(self.client, name)
            if callable(attr):
                return self.wrap(attr)
            return attr
        except Exception as e:
            abort(400, str(e))

    def wrap(self, func):
        def outer(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "token has expired" in str(e):
                    logout_user()
                    abort(401, str(e))
                else:
                    abort(400, str(e))
        return outer


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
