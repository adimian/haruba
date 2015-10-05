from . import ProtectedResource
from collections import defaultdict
from flask_login import LoginManager
from flask import current_app, session
from flask_restful import Resource, reqparse
from flask_login import login_user, current_user, logout_user
from flask_principal import Identity, identity_changed, abort
from ..utils import WrappedSigilClient, get_sigil_client
from ..permissions import is_admin

login_manager = LoginManager()


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

    def user_details(self, get_api_key=True):
        client = get_sigil_client()
        details = client.user_details()
        if get_api_key:
            details['api_key'] = client.get_api_key()
        zones = []
        for key, values in current_user.zones.items():
            zones.append({"zone": key, "access": values})
        details['provides'] = zones
        return details


def request_authentication(username, password, totp, api_key):
    app_name = current_app.config['SIGIL_APP_NAME']
    client = WrappedSigilClient(username=username, password=password,
                                api_key=api_key)
    client.login(totp=totp)
    session['sigil_token'] = client._token
    details = client.user_details()
    details.update(client.provides(context=app_name))
    return details


@login_manager.user_loader
def load_user(login):
    return User(login, {})


class Login(Resource):
    def get(self):
        # for the JS lib to know if the user is logged in or not
        return {"authenticated": current_user.is_authenticated(),
                "admin": is_admin()}

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('login', type=str)
        parser.add_argument('password', type=str)
        parser.add_argument('totp', type=str)
        # OR
        parser.add_argument('api_key', type=str)
        args = parser.parse_args()

        if not (args.get('login') or args.get('api_key')):
            abort(400, "Must provide login or api key")
        # let sigil take care of the other error handling,
        # just relay the message to the user
        user = request_authentication(args.get('login'), args.get('password'),
                                      args.get('totp'), args.get('api_key'))
        if user.get('username'):
            login = user['username']
            login_user(User(login, user['provides']))
            session['provides'] = user['provides']
            identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(login))
            return ("success", 200)
        abort(401, "Could not log in")


class Logout(ProtectedResource):
    def get(self):
        logout_user()


class UserDetails(ProtectedResource):
    def get(self):
        return current_user.user_details()
