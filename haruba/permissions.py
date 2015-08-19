from flask import abort, session
from flask_principal import Principal
from flask_login import current_user
from flask_principal import identity_loaded, UserNeed, Permission
from functools import wraps
from haruba.utils import get_group_root

principal = Principal()
ZONE_CONTEXT = 'zone'
ADMIN_CONTEXT = 'permissions'

READ_PERMISSION = 'read'
WRITE_PERMISSION = 'write'


def process_request(func, args, kwargs, context, permission):
    group = kwargs.get('group', None)
    if group:
        need = tuple((context, permission, group))
    else:
        need = tuple((context, permission))

    permission = Permission(need)
    if permission.can():
        if group:
            # already setting the group root
            # to prevent from getting it manually in each resource
            kwargs['group_root'] = get_group_root(group)
        return func(*args, **kwargs)
    abort(403)


def has_read(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        return process_request(func, args, kwargs,
                               ZONE_CONTEXT, READ_PERMISSION)
    return decorated_view


def has_write(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        return process_request(func, args, kwargs,
                               ZONE_CONTEXT, WRITE_PERMISSION)
    return decorated_view


def has_admin_read(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        return process_request(func, args, kwargs,
                               ADMIN_CONTEXT, READ_PERMISSION)
    return decorated_view


def has_admin_write(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        return process_request(func, args, kwargs,
                               ADMIN_CONTEXT, WRITE_PERMISSION)
    return decorated_view


def set_identity_loader(app):
    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        identity.user = current_user

        if hasattr(current_user, 'login'):
            identity.provides.add(UserNeed(current_user.login))

        for role in session.get('provides', []):
            identity.provides.add(tuple(role))
