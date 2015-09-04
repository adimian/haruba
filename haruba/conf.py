from os import environ


def configure(app):
    config = app.config

    def set_default(key, value):
        v = environ.get(key, value)
        try:
            v = int(v)
        except:
            pass
        if isinstance(v, str):
            if v.lower() in ('false', 'no'):
                v = False
            elif v.lower() in('true', 'yes'):
                v = True
        config[key] = v

    set_default('DEBUG', False)
    set_default('HOST', '0.0.0.0')
    set_default('CSRF_ENABLED', True)
    set_default('PORT', 5000)
    set_default('API_URL_PREFIX', '')
    set_default('SERVER_NAME', 'docker.dev')
    set_default('SQLALCHEMY_DATABASE_URI', 'sqlite:///')
    set_default('SECRET_KEY', 'secret-key')
    set_default('SENTRY_DSN', '')

    set_default('SIGIL_APP_KEY', '')
    set_default('SIGIL_API_URL', 'http://sigil:5000')
    set_default('SIGIL_APP_NAME', 'haruba')
    set_default('HARUBA_SERVE_ROOT', '/tmp/haruba')
    set_default('HARUBA_ZONE_DEFAULT', 'data')
    set_default('PERMANENT_SESSION_LIFETIME', 7200)


