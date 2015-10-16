from chmod.connection import Receiver
from chmod.conf import configure
from chmod import logger
import json
import grp
import os

config = {}
configure(config)


class ReceivedMessageHandler(object):
    def __init__(self, connection):
        self.connection = connection

    def __call__(self, ch, method, properties, body):
        logger.info('received %r', body)
        try:
            logger.info("decoding body")
            message = json.loads(body.decode('utf-8'))
            logger.info("processing message")
            self._call(ch, method, message)
        except Exception as e:
            logger.error(e)
            # skip job
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def _call(self, ch, method, message):
        for path in message:
            self.change_file_permission(path)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def change_file_permission(self, path):
        perm_gid = grp.getgrnam(config['CHMOD_GROUP']).gr_gid
        if os.path.exists(path):
            try:
                os.chown(path, -1, perm_gid)
                logger.info('chown of %s successful', path)
            except OSError:
                logger.exception('unable to chown %s', path)

            try:
                if os.path.isdir(path):
                    os.chmod(path, config['CHMOD_FOLDER_PERMISSIONS'])
                else:
                    os.chmod(path, config['CHMOD_FILE_PERMISSIONS'])
                logger.info('chmod of %s successful', path)
            except OSError:
                logger.exception('unable to chmod %s', path)
        else:
            logger.warning('%s cannot be found on the filesystem', path)

receiver = Receiver(config)
receiver.listen(ReceivedMessageHandler)
