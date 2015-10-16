from contextlib import contextmanager
import pika
import time
import json
from . import logger


class Base(object):
    def __init__(self, config):
        self.username = config['CHMOD_AMQP_USER']
        self.password = config['CHMOD_AMQP_PASSWORD']
        self.hostname = config['CHMOD_AMQP_HOST']
        self.queue_name = config['CHMOD_QUEUE_NAME']
        self.slots = config['CHMOD_SLOTS']

    def connect(self, timeout):
        credentials = pika.PlainCredentials(
            self.username,
            self.password,
        )
        parameters = pika.ConnectionParameters(
            host=self.hostname,
            credentials=credentials,
        )
        try:
            connection = pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError as error:
            logger.error("Could not connect. Retrying in %ss" % timeout)
            time.sleep(timeout)
            return False, error
        return True, connection

    def get_connection(self):
        timeout = 1
        while timeout <= 8:
            connected, connection = self.connect(timeout)
            if connected:
                break
            else:
                timeout = timeout * 2

        if not connected:
            raise connection
        return connection


class Receiver(Base):
    def listen(self, handler):
        connection = self.get_connection()
        channel = connection.channel()

        queue_name = self.queue_name

        channel.queue_declare(queue=queue_name, durable=True)
        logger.info('---')
        logger.info('--- Listening for incoming messages.')
        logger.info('---')

        channel.basic_qos(prefetch_count=int(self.slots))
        channel.basic_consume(handler(connection),
                              queue=queue_name)
        channel.start_consuming()


class Sender(Base):
    @contextmanager
    def open_channel(self):
        connection = self.get_connection()
        channel = connection.channel()
        yield channel
        connection.close()

    def send(self, message):
        if not isinstance(message, str):
            message = json.dumps(message)
        with self.open_channel() as channel:
            channel.queue_declare(queue=self.queue_name, durable=True)
            properties = pika.BasicProperties(delivery_mode=2,)
            channel.basic_publish(exchange='',
                                  routing_key=self.queue_name,
                                  body=message,
                                  properties=properties)
