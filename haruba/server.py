from flask_script import Manager, Server, prompt_pass, prompt
from sigil_client import SigilClient
from flask_alembic.cli.script import manager as alembic_manager

from haruba.database import db
from haruba.api import app, setup_endpoints, alembic
import logging
logger = logging.getLogger('haruba.server')

setup_endpoints()

manager = Manager(app)
manager.add_command("runserver", Server(host=app.config['HOST'],
                                        port=app.config['PORT']))
manager.add_command('db', alembic_manager)


def register_app(url, app_name, credentials):
    client = SigilClient(url, **credentials)
    client.login()
    app_key = client.new_app(app_name)
    print(app_key)


@manager.command
def init():
    alembic.upgrade()


@manager.command
def register():
    username = prompt('haruba admin username (must exist in sigil)')
    password = prompt_pass('haruba admin password')
    if username and password:
        register_app(url=app.config['SIGIL_API_URL'],
                     app_name=app.config['SIGIL_APP_NAME'],
                     credentials={'username': username,
                                  'password': password})
    else:
        print('no username or password given, aborting')

if __name__ == "__main__":
    manager.run()
