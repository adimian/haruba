from flask_script import Manager, Server, prompt_pass, prompt
from sigil_client import SigilClient, SigilApplication

from haruba.database import db
from haruba.harubad import app


@app.before_first_request
def create_db():
    db.create_all()


manager = Manager(app)
manager.add_command("runserver", Server(host=app.config['HOST'],
                                        port=app.config['PORT']))


def register_app(url, app_name, credentials):
    client = SigilClient(url, **credentials)
    client.login()
    app_key = client.new_app(app_name)
    application = SigilApplication(url, app_key)

    needs = (('zone', 'write'),
             ('zone', 'read'))
    updated_needs = application.declare(needs)
    print(updated_needs)


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
        print('aborting')

if __name__ == "__main__":
    manager.run()
