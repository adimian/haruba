from os import environ, path


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

    set_default('DEBUG', True)
    set_default('HOST', '0.0.0.0')
    set_default('CSRF_ENABLED', True)
    set_default('CORS_ORIGINS', '')
    set_default('PORT', 5000)
    set_default('STANDALONE', False)
    set_default('ERROR_404_HELP', False)
    set_default('API_URL_PREFIX', '')
    set_default('SERVER_NAME', None)
    set_default('SQLALCHEMY_DATABASE_URI', 'sqlite:///')
    set_default('SECRET_KEY', 'secret-key')
    set_default('SENTRY_DSN', '')
    set_default('SERVE_STATIC', False)
    set_default('UI_URL_PREFIX', '')
    set_default('APP_KEYS_FOLDER', '')

    set_default('SIGIL_APP_KEY', '')
    set_default('SIGIL_BASE_URL', '')
    set_default('SIGIL_API_URL', '%s/sigil-api' % config['SIGIL_BASE_URL'])  # no trailing slash
    set_default('PRIV_SIGIL_API_URL', config['SIGIL_API_URL'])
    set_default('SIGIL_UI_URL', '%s/sigil' % config['SIGIL_BASE_URL'])
    set_default('SIGIL_APP_NAME', 'haruba')
    set_default('HARUBA_SERVE_ROOT', '/tmp/haruba')
    set_default('HARUBA_ZONE_DEFAULT', 'data')
    set_default('HARUBA_PLUGIN_FOLDER', '')
    set_default('HARUBA_ENABLE_PLUGINS', False)
    set_default('PERMANENT_SESSION_LIFETIME', 7200)

    if config['APP_KEYS_FOLDER'] and not config['SIGIL_APP_KEY']:
        keyfile = path.join(config['APP_KEYS_FOLDER'],
                            '{}.appkey'.format(config['SIGIL_APP_NAME']))
        with open(keyfile, 'r') as f:
            config['SIGIL_APP_KEY'] = f.read()
