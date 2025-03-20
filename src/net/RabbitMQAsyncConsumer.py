import pika
import json
from .__init__ import dict_to_frameobjekt
from src.cam.Showxating.lib.FrameObjektEncoder import ObjektEncoder
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

            # def dict_to_frameobjekt(data):
            #     """Convert dictionary back to FrameObjekt."""
            #     frame_obj = FrameObjekt.create(data['f_id'])
            #     frame_obj.timestamp = datetime.fromisoformat(data['timestamp'])
            #     frame_obj.tag = data['tag']
            #
            #     # frame_obj.contours = np.array(data['contours']) if data['contours'] is not None else None
            #     # frame_obj.hierarchy = np.array(data['hierarchy']) if data['hierarchy'] is not None else None
            #     # frame_obj.prev_tag = data['prev_tag']
            #     # frame_obj.contour_id = data['contour_id']
            #     frame_obj.curr_dist = data['curr_dist']
            #     # frame_obj.distances = np.array(data['distances'])
            #     frame_obj.fd = data['fd']
            #     frame_obj.fd_mean = data['fd_mean']
            #     # frame_obj.delta_range = data['delta_range']
            #     frame_obj.hist_delta = data['hist_delta']
            #     # frame_obj.f_hist = data['f_hist']
            #     frame_obj.w_hist = data['w_hist']  # DBUG this needed to be an array, so this isn't the right way to process this
            #     frame_obj.rect = tuple(data['rect']) if data['rect'] else None
            #     frame_obj.avg_loc = np.array(data['avg_loc'])
            #     frame_obj.dist_mean = data['dist_mean']
            #     # frame_obj.wall = np.array(data['wall']) if data['wall'] is not None else None
            #     frame_obj.close = data['close']
            #     frame_obj.inside_rect = data['inside_rect']
            #     frame_obj.hist_pass = data['hist_pass']
            #     frame_obj.wall_pass = data['wall_pass']
            #     return frame_obj

            frame_obj = dict_to_frameobjekt(data)

            # Start encoder thread to process frame
            encoder = ObjektEncoder(frame_obj)
            encoder.start()

            # Acknowledge message after processing starts
            self.channel.basic_ack(delivery_tag=method.delivery_tag)
            logging.info(f"Acknowledged frame {frame_obj.f_id}")

        except Exception as e:
            logging.error(f"Failed to process message: {e}")

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
    consumer = RabbitMQAsyncConsumer()
    consumer.run()
