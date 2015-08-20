from flask import Flask, send_from_directory
from raven.contrib.flask import Sentry
import os

from haruba.api import haruba_api, login_manager
from haruba.permissions import principal, set_identity_loader
from haruba.database import db
OVERRIDES = ('SECRET_KEY',
             'SENTRY_DSN')


def read_config(config, key):
    config[key] = os.environ.get(key, config[key])


def make_app(config=None):
    if not config:
        config = 'config.Config'
    app = Flask(__name__)
    app.config.from_object(config)
    app.config.from_envvar('HARUBA_CONFIG', silent=True)
    for key in OVERRIDES:
        read_config(app.config, key)

    @app.route('/')
    @app.route('/<path:path>')
    def serve(path=""):
        file = os.path.basename(path)
        path = os.path.dirname(path)
        if not file:
            file = 'index.html'
        path = os.path.join('haruba_ui', path)
        return send_from_directory(path, file)

    haruba_api.init_app(app)
    principal.init_app(app)
    set_identity_loader(app)
    login_manager.init_app(app)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    if app.config['SENTRY_DSN']:
        Sentry(app)
    else:
        print("sentry not enabled !")

    return app


if __name__ == '__main__':
    app = make_app()
    app.run(host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'])
else:
    app = make_app()
