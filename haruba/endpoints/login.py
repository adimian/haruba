from . import ProtectedResource
from collections import defaultdict
from flask_login import LoginManager
from sigil_client import SigilClient
from flask import current_app, session
from flask_restful import Resource, reqparse
from flask_login import login_user, current_user, logout_user
from flask_principal import Identity, identity_changed, abort
from ..utils import WrappedSigilClient

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


def request_authentication(username, password):
    app_name = current_app.config['SIGIL_APP_NAME']
    client = WrappedSigilClient(username=username, password=password)
    client.login()
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
        return current_user.is_authenticated()

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('login', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        args = parser.parse_args()

        login = args['login']
        user = request_authentication(login, args['password'])
        if user.get('username'):
            login_user(User(user['username'], user['provides']))
            session['provides'] = user['provides']
            identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(login))
            return ("success", 200)
        abort(401, "Could not log in")


class Logout(ProtectedResource):
    def get(self):
        logout_user()
