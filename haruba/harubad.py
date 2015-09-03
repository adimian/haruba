import os

from flask import Flask, send_from_directory
from raven.contrib.flask import Sentry

from .api import haruba_api, login_manager
from .conf import configure
from .database import db
from .permissions import principal, set_identity_loader


app = Flask(__name__)
configure(app)


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
