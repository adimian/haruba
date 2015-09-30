import logging
import sys
import os

from flask import Flask, send_from_directory, safe_join
from flask_restful import Api
from flask_alembic import Alembic
from raven.contrib.flask import Sentry

from .endpoints.permission import Permissions
from .endpoints.login import Login, login_manager, Logout, UserDetails
from .endpoints.folder import Folder
from .endpoints.zone import MyZones, Zones
from .endpoints.transfer import Upload, Download
from .endpoints.command import Command
from .conf import configure
from .database import db
from .permissions import principal, set_identity_loader


app = Flask(__name__)
configure(app)

if app.config['DEBUG']:
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(app.name)

principal.init_app(app)
set_identity_loader(app)
login_manager.init_app(app)
db.init_app(app)
alembic = Alembic(app)

sentry = None
if app.config['SENTRY_DSN']:
    logger.info('Sentry is active')
    sentry = Sentry(app)
else:
    logger.info('Sentry is inactive')

if app.config['SERVE_STATIC']:
    # static files
    @app.route('{}/'.format(app.config['UI_URL_PREFIX']))
    @app.route('{}/<path:path>'.format(app.config['UI_URL_PREFIX']))
    def serve(path=""):
        d = os.path.dirname
        root = d(d(os.path.abspath(__file__)))
        file = os.path.basename(path)
        path = d(path)
        if not file:
            file = 'index.html'
        path = safe_join(safe_join(root, 'ui'), path)
        print(path, file)
        return send_from_directory(path, file)


def setup_endpoints():
    logger.info('setting up endpoints')
    api = Api(app, prefix=app.config['API_URL_PREFIX'])
    api.add_resource(Login, '/login')
    api.add_resource(Logout, '/logout')
    api.add_resource(UserDetails, '/user/details')
    api.add_resource(Folder, '/files/<group>', '/files/<group>/<path:path>')
    api.add_resource(Upload, '/upload/<group>', '/upload/<group>/<path:path>')
    api.add_resource(Download,
                     '/download/<group>',
                     '/download/<group>/<path:path>')
    api.add_resource(Command,
                     '/command/<group>',
                     '/command/<group>/<path:path>')
    api.add_resource(MyZones, '/myzones')
    api.add_resource(Zones, '/zone')
    api.add_resource(Permissions, '/permissions')
    logger.info('endpoints setup done')
