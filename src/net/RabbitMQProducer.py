# Version: 1.1.0
# Description: RabbitMQ producer for sending FrameObjekt instances as JSON messages.
# Uses pika for RabbitMQ communication.
# Message persistence enabled for reliability.
# Logging added for better monitoring and debugging.

import pika
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s')


class RabbitMQProducer:

    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='frame_queue', durable=True)

    def send_frameobjekt(self, frame_obj):

        def frameobjekt_to_dict(f_obj):
            """Convert FrameObjekt to a serializable dictionary."""
            return {
                'f_id': f_obj.f_id,
                'timestamp': f_obj.timestamp.isoformat(),
                'tag': f_obj.tag,

                # 'contours': f_obj.contours.tolist() if f_obj.contours is not None else None,
                # 'hierarchy': f_obj.hierarchy.tolist() if f_obj.hierarchy is not None else None,
                # 'prev_tag': f_obj.prev_tag,
                # 'contour_id': f_obj.contour_id,
                'curr_dist': f_obj.curr_dist,
                # 'distances': f_obj.distances.tolist(),
                'fd': f_obj.fd,
                'fd_mean': f_obj.fd_mean,
                # 'delta_range': f_obj.delta_range,
                'hist_delta': f_obj.hist_delta,
                # 'f_hist': f_obj.f_hist,
                'w_hist': f_obj.w_hist.tolist(),
                'rect': f_obj.rect,
                'avg_loc': f_obj.avg_loc.tolist(),
                'dist_mean': f_obj.dist_mean,
                # 'wall': f_obj.wall.tolist() if f_obj.wall is not None else None,
                'close': str(f_obj.close),
                'inside_rect': str(f_obj.inside_rect),
                'hist_pass': str(f_obj.hist_pass),
                'wall_pass': str(f_obj.wall_pass)
            }

        """Send FrameObjekt data to RabbitMQ."""
        try:
            message = json.dumps(frameobjekt_to_dict(frame_obj))
            self.channel.basic_publish(
                exchange='',
                routing_key='frame_queue',
                body=bytes(message, encoding='utf_8'),
                properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
            )
            logging.info(f"Sent frame {frame_obj.f_id} successfully")
        except Exception as e:
            logging.error(f"Failed to send frame {frame_obj.f_id}: {e}")

