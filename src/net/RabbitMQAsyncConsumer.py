from datetime import datetime

import pika
import json

from pika.exceptions import AMQPConnectionError

from src.net.lib.net_utils import dict_to_frameobjekt
from src.cam.Showxating.lib.FrameObjektEncoder import FrameObjektEncoder
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s')


class RabbitMQAsyncConsumer:
    """RabbitMQ Consumer using SelectConnection (async)."""

    def __init__(self):
        self.connection = None
        self.channel = None

    def on_channel_open(self, channel):
        """Callback when the channel is successfully opened."""
        logging.info("Channel opened")

        # Declare queue to ensure it exists
        self.channel = channel
        channel.queue_declare(queue='frame_queue', durable=True, callback=self.on_queue_declared)

    def on_queue_declared(self, _):
        """Callback after queue declaration."""
        logging.info("Queue declared, starting consumption...")

        # Start consuming messages from the queue
        self.channel.basic_consume(queue='frame_queue', on_message_callback=self.on_message)

    def on_connection_open(self, connection):
        """Callback when the connection is successfully opened."""
        logging.info("Connection opened")
        self.connection = connection
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_error(self, _connection, error_message=None):
        """Callback when a connection error occurs."""
        logging.error(f"Connection error: {error_message}")

    def on_message(self, channel, method, properties, body):
        """Callback function for processing messages."""
        try:
            data = json.loads(body)

            frame_obj = dict_to_frameobjekt(data)

            # Start encoder thread to process frame
            encoder = FrameObjektEncoder(frame_obj)
            encoder.start()

            self.channel.basic_ack(delivery_tag=method.delivery_tag)

            created_time = datetime.fromisoformat(frame_obj['created'])
            time_diff = (datetime.now() - created_time).total_seconds()

            logging.info(f"Received {frame_obj['f_id']}, time_diff={time_diff:.6f}s")
        except Exception as e:
            logging.error(f"Failed to process message: {e}")

    def run(self):
        """Start the asynchronous consumer."""
        logging.info("Starting consumer...")
        parameters = pika.ConnectionParameters(host='localhost')

        try:
            self.connection = pika.SelectConnection(
                    parameters=parameters,
                    on_open_callback=self.on_connection_open,
                    on_open_error_callback=self.on_connection_error
            )
            logging.info("Starting event loop...")
            self.connection.ioloop.start()
        except KeyboardInterrupt:
            logging.info("Interrupted. Closing connection...")
            self.connection.close()

if __name__ == "__main__":
    consumer = RabbitMQAsyncConsumer()
    consumer.run()
