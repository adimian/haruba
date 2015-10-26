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
        self.perm_gid = grp.getgrnam(config['CHMOD_GROUP']).gr_gid
        self.folder_chmod = int(str(config['CHMOD_FOLDER_PERMISSIONS']), 8)
        self.file_chmod = int(str(config['CHMOD_FILE_PERMISSIONS']), 8)

    def __call__(self, ch, method, properties, body):
        try:
            message = json.loads(body.decode('utf-8'))
            self._call(ch, method, message)
        except Exception as e:
            logger.error(e)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def _call(self, ch, method, message):
        for path in message:
            self.change_file_permission(path)

    def change_file_permission(self, path):
        if os.path.exists(path):
            try:
                os.chown(path, -1, self.perm_gid)
                logger.info('chown of %s successful', path)
            except OSError:
                logger.exception('unable to chown %s', path)

            try:
                if os.path.isdir(path):
                    os.chmod(path, self.folder_chmod)
                else:
                    os.chmod(path, self.file_chmod)
                logger.info('chmod of %s successful', path)
            except OSError:
                logger.exception('unable to chmod %s', path)
        else:
            logger.warning('%s cannot be found on the filesystem', path)

receiver = Receiver(config)
receiver.listen(ReceivedMessageHandler)
