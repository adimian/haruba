from os import environ


def configure(config):
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

    set_default('CHMOD_OWNER', 'root')
    set_default('CHMOD_GROUP', 'staff')
    set_default('CHMOD_FILE_PERMISSIONS', '0660')
    set_default('CHMOD_FOLDER_PERMISSIONS', '0770')

    set_default('CHMOD_AMQP_USER', 'guest')
    set_default('CHMOD_AMQP_PASSWORD', 'guest')
    set_default('CHMOD_AMQP_HOST', 'localhost')
    set_default('CHMOD_QUEUE_NAME', 'chmod')
    set_default('CHMOD_SLOTS', 4)
