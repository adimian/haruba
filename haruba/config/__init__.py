class Config(object):
    HOST = 'localhost'
    PORT = 5000
    DEBUG = True
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'you-will-never-get-me'
    SENTRY_DSN = ''
    SIGIL_API_KEY = ''
    HARUBA_SERVE_ROOT = '/srv'
    HARUBA_ZONE_DEFAULT = 'data'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
