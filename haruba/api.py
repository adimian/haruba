import logging

from flask import abort, current_app, session
from flask_login import login_required, login_user
from flask_restful import Resource, Api, reqparse
from flask_login import LoginManager
from flask_principal import Identity, identity_changed

from haruba.utils import User
from haruba.permissions import user_in_group

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG

haruba_api = Api()
login_manager = LoginManager()


def request_authentication(username, password):
    # connect to identity server and authenticate the user
    return {'login': 'test',
            'firstname': 'Some',
            'lastname': 'User',
            'provides': {'groups': ('some_group', 'admin')}}


@login_manager.user_loader
def load_user(login):
    return User(login, {})


class Login(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('login', type=str, required=True)
        parser.add_argument('password', type=str, required=True)
        args = parser.parse_args()

        login = args['login']
        user = request_authentication(login, args['password'])
        if user.get('login'):
            login_user(User(user['login'], user['provides']))
            session['provides'] = user['provides']
            identity_changed.send(current_app._get_current_object(),
                                  identity=Identity(login))
            return {'status': 'success'}
        abort(401)


class ProtectedResource(Resource):
    method_decorators = [login_required, user_in_group]


class Folder(ProtectedResource):
    def get(self, group):
        # download
        return {'status': 'group files'}

    def post(self):
        # upload
        pass


haruba_api.add_resource(Login,
                        '/login')
haruba_api.add_resource(Folder,
                        '/files/<group>/')
