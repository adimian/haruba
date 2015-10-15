import os
import zipfile

from flask import current_app, jsonify, session, abort
from flask_login import logout_user, current_user
from sigil_client import SigilClient
from functools import wraps

from .database import db, Zone
from .signals import new_file_or_folder


FILE_TYPE = 'file'
FOLDER_TYPE = 'folder'


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated():
            return current_app.login_manager.unauthorized()
        # adding the user to the sentry context
        from .api import sentry
        if sentry:
            sentry.user_context(current_user.user_details(get_api_key=False))

        return func(*args, **kwargs)
    return decorated_view


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


def get_group_root(group_name):
    server_root = current_app.config['HARUBA_SERVE_ROOT']
    zone = db.session.query(Zone).filter_by(name=group_name).one()
    return os.path.join(server_root, zone.path)


def unzip(zip_dir, path, delete_after=False):
    if os.path.exists(zip_dir):
        with zipfile.ZipFile(zip_dir) as zf:
            zf.extractall(path)
            new_file_or_folder.send(current_app._get_current_object(),
                                    path=path)
        if delete_after:
            os.remove(zip_dir)
