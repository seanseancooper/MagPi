# Version: 1.2.0
# Description: RabbitMQ asynchronous consumer for processing FrameObjekt instances.
# Uses pika.SelectConnection for non-blocking message consumption.
# Encoder runs in a separate thread for parallel processing.
# Logging added for better monitoring and debugging.

import pika
import json
from RabbitMQConsumer import ObjektEncoder, dict_to_frameobjekt

import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s')


class Consumer:
    """RabbitMQ Consumer using SelectConnection (async)."""

    def __init__(self):
        self.connection = None
        self.channel = None

    def on_message(self, channel, method, properties, body):
        """Callback function for processing messages."""
        try:
            data = json.loads(body)

            frame_obj = dict_to_frameobjekt(data)

            # Start encoder thread to process frame
            encoder = ObjektEncoder(frame_obj)
            encoder.start()

            # Acknowledge message after processing starts
            channel.basic_ack(delivery_tag=method.delivery_tag)
            logging.info(f"Acknowledged frame {frame_obj.f_id}")

        except Exception as e:
            logging.error(f"Failed to process message: {e}")

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

    def run(self):
        """Start the asynchronous consumer."""
        logging.info("Starting consumer...")

        parameters = pika.ConnectionParameters(host='localhost')
        self.connection = pika.SelectConnection(
                parameters=parameters,
                on_open_callback=self.on_connection_open,
                on_open_error_callback=self.on_connection_error
        )

        try:
            logging.info("Starting event loop...")
            self.connection.ioloop.start()
        except KeyboardInterrupt:
            logging.info("Interrupted. Closing connection...")
            self.connection.close()
            self.connection.ioloop.start()


if __name__ == "__main__":
    consumer = Consumer()
    consumer.run()
