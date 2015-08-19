#! /usr/bin/env python3
from argparse import ArgumentParser
from sigil_client import SigilClient, SigilApplication


# Action define a cli action
class Action:
    actions = {}

    def __init__(self, *required, optional=None):
        self.required = required
        self.optional = optional

    def __call__(self, fn):
        self.name = fn.__name__
        self.actions[self.name] = self
        self.fn = fn
        self.help = fn.__doc__
        return fn

    @classmethod
    def get(cls, name, default=None):
        return cls.actions.get(name, default)

    @classmethod
    def all(cls):
        return sorted(cls.actions.keys())

    def launch(self, *args, **kwars):
        if len(args) < len(self.required):
            print('Error: %s need at least %s arguments' % (
                self.name, len(self.required)))
            return
        return self.fn(*args, **kwars)


@Action(optional='action')
def help(action_name=None):
    """
    ------------------------------------------------
    this help text all over again

    """

    if action_name and Action.get(action_name):
        actions = [action_name]
    else:
        actions = Action.all()
    for action_name in actions:
        action = Action.get(action_name)
        print('   %s: %s' % (action_name, action.help))


@Action('sigil url', 'api key', optional='app name')
def api_register(sigil_url, api_key, app_name='haruba'):
    """
    ------------------------------------------------
    Register through user api key.
    The user used will have admin rights.
    required:
      - sigil url: url to the sigil application
      - api key: api key to use
    optional:
      - app name: The application name you want to register on sigil.
                  Defaults to 'haruba'

    """
    creds = {"api_key": api_key}
    register_app(sigil_url, app_name, creds)


@Action('sigil url', 'username', 'password', optional='app name')
def login_register(sigil_url, username, password, app_name='haruba'):
    """
    ------------------------------------------------
    Register through user login credentials.
    The user used will have admin rights
    required:
      - sigil url: url to the sigil application
      - username: Username to use
      - password: Password to use
    optional:
      - app name: The application name you want to register on sigil.
                  Defaults to 'haruba'

    """
    creds = {"username": username,
             "password": password}
    register_app(sigil_url, app_name, creds)


def register_app(url, app_name, credentials):
    client = SigilClient(url, **credentials)
    client.login()
    app_key = client.new_app(app_name)
    application = SigilApplication(url, app_key)

    needs = (('zone', 'write'),
             ('zone', 'read'))
    updated_needs = application.declare(needs)
    print(updated_needs)


if __name__ == '__main__':
    action_list = ', '.join(Action.all())
    parser = ArgumentParser(
        description='Registers haruba on sigil',
    )
    parser.add_argument(
        'action', nargs='+', help='One of: %s' % action_list)
    args = parser.parse_args()

    action_name = args.action[0]
    action = Action.get(action_name)
    if action is None:
        parser.error('Unknown action "%s"' % action_name)
    action.launch(*args.action[1:])
