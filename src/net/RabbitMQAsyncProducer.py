import pika
import json
import logging
from src.net.lib.net_utils import frameobjekt_to_dict

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s')


class RabbitMQAsyncProducer:
    """RabbitMQ Producer using SelectConnection (async)."""

    def __init__(self):
        self.connection = None
        self.channel = None

    def on_channel_open(self, channel):
        """Callback when the channel is opened."""
        logging.info("Channel opened")
        self.channel = channel

        # Declare queue to ensure it exists
        self.channel.queue_declare(queue='frame_queue', durable=True, callback=self.on_queue_declared)

    def on_queue_declared(self, _):
        """Callback when the queue is declared."""
        logging.info("Queue declared, ready to publish messages.")
        # from src.cam.Showxating.lib.FrameObjekt import FrameObjekt
        # import numpy as np

        # Example: Send a test FrameObjekt
        # frame_obj = FrameObjekt.create(f_id=1)
        # frame_obj.tag = FrameObjekt.create_tag(frame_obj.f_id)
        # frame_obj.avg_loc = np.array([100, 200])
        # frame_obj.fd = 12.5
        #
        # Publish message
        # self.publish_message(frame_obj)

    def on_connection_open(self, connection):
        """Callback when the connection is opened."""
        logging.info("Connection opened")
        self.connection = connection

        # Open channel after connection is established
        self.connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_error(self, _connection, error_message=None):
        """Callback when a connection error occurs."""
        logging.error(f"Connection error: {error_message}")

    def publish_message(self, frame_obj):

        # def frameobjekt_to_dict(f_obj):
        #     """Convert FrameObjekt to a serializable dictionary."""
        #     return {
        #         'f_id': f_obj.f_id,
        #         'timestamp': f_obj.timestamp.isoformat(),
        #         'tag': f_obj.tag,
        #
        #         # 'contours': f_obj.contours.tolist() if f_obj.contours is not None else None,
        #         # 'hierarchy': f_obj.hierarchy.tolist() if f_obj.hierarchy is not None else None,
        #         # 'prev_tag': f_obj.prev_tag,
        #         # 'contour_id': f_obj.contour_id,
        #         'curr_dist': f_obj.curr_dist,
        #         # 'distances': f_obj.distances.tolist(),
        #         'fd': f_obj.fd,
        #         'fd_mean': f_obj.fd_mean,
        #         # 'delta_range': f_obj.delta_range,
        #         'hist_delta': f_obj.hist_delta,
        #         # 'f_hist': f_obj.f_hist,
        #         'w_hist': f_obj.w_hist.tolist() if f_obj.w_hist is not None else [[[]]],  # DBUG this needs to be an array, so this isn't the right way to process this
        #         'rect': f_obj.rect,
        #         'avg_loc': f_obj.avg_loc.tolist(),
        #         'dist_mean': f_obj.dist_mean,
        #         # 'wall': f_obj.wall.tolist() if f_obj.wall is not None else None,
        #         'close': str(f_obj.close),
        #         'inside_rect': str(f_obj.inside_rect),
        #         'hist_pass': str(f_obj.hist_pass),
        #         'wall_pass': str(f_obj.wall_pass)
        #     }

        """Publish a message to the queue."""
        try:
            message = json.dumps(frameobjekt_to_dict(frame_obj))
            self.channel.basic_publish(
                exchange='',
                routing_key='frame_queue',
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2  # Make message persistent
                )
            )
            logging.info(f"Sent frame {frame_obj.f_id} successfully")
        except Exception as e:
            logging.error(f"Failed to send frame {frame_obj.f_id}: {e}")

    def run(self):
            """Start the asynchronous producer."""
            logging.info("Starting producer...")

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
    producer = RabbitMQAsyncProducer()
    producer.run()

