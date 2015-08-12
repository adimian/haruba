from flask import abort, session
from flask_principal import Principal
from flask_login import current_user
from flask_principal import (identity_loaded, RoleNeed, UserNeed,
                             Permission)
from functools import wraps

principal = Principal()


def user_in_group(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        permission = Permission(RoleNeed(kwargs['group']))
        if permission.can():
            return func(*args, **kwargs)
        abort(403)
    return decorated_view


def set_identity_loader(app):
    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        identity.user = current_user
        print('loading the identity')
        print(session['provides'])

        if hasattr(current_user, 'login'):
            identity.provides.add(UserNeed(current_user.login))

        for role in session.get('provides', {}).get('groups', []):
            identity.provides.add(RoleNeed(role))
