from datetime import timedelta


class Config(object):
    HOST = 'localhost'
    PORT = 5000
    DEBUG = True
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'you-will-never-get-me'
    SENTRY_DSN = ''
    SIGIL_APP_KEY = ('WzIsImZmMjM5YzU0ZDBmMzBlNDQ2N2ZmNGYzN2M5NmNkZmQxIl0.'
                     'CLykAQ.y3EL8egof4oW9TkSRHvkYgXJTx4')
    SIGIL_API_URL = 'http://192.168.111.192:5000'
    SIGIL_APP_NAME = 'haruba'
    HARUBA_SERVE_ROOT = '/tmp/haruba'
    HARUBA_ZONE_DEFAULT = 'data'
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/haruba.db'

    PERMANENT_SESSION_LIFETIME = timedelta(seconds=7200)


class TestConfig(Config):
        SQLALCHEMY_DATABASE_URI = 'sqlite:///'
