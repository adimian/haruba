class Config(object):
    HOST = 'localhost'
    PORT = 5000
    DEBUG = True
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'you-will-never-get-me'
    SENTRY_DSN = ''
    SIGIL_APP_KEY = 'WzIsImZmMjM5YzU0ZDBmMzBlNDQ2N2ZmNGYzN2M5NmNkZmQxIl0.CLX1tg.ya0imyWozuOb0VbFqJf7TLrL3WY'
    SIGIL_API_URL = ''
    SIGIL_APP_NAME = 'haruba'
    HARUBA_SERVE_ROOT = '/srv'
    HARUBA_ZONE_DEFAULT = 'data'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
