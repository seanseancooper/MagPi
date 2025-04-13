import asyncio
import threading
from flask import Flask
from flask_cors import CORS

import routes
from src.lib.rest_server import RESTServer


class ARXController(threading.Thread):

    def __init__(self):
        super().__init__()

    @staticmethod
    def create_app():
        """Create Flask application."""
        app = Flask('arx',
                    instance_relative_config=True,
                    subdomain_matching=True)

        cors = CORS(app)
        app.config['CORS_HEADERS'] = 'Content-Type'

        with app.app_context():
            if __name__ == '__main__':
                app.config['SERVER_NAME'] = routes.arxRec.config['SERVER_NAME']
                app.config['DEBUG'] = routes.arxRec.config['DEBUG']
                app.register_blueprint(routes.arx_bp)
            return app

    def run(self) -> None:
        try:
            import atexit

            def stop():

                from src.arx.lib.ARXSignalPoint import ARXSignalPoint
                arxs = ARXSignalPoint(routes.arxRec.get_worker_id(),
                                      routes.arxRec.lon,
                                      routes.arxRec.lat,
                                      routes.arxRec.signal_cache[:-1]) #remove signal_cache

                out = routes.arxRec.stop()  # required.

                def get_audio_data(f):
                    import soundfile as sf
                    return sf.read(f)

                data, sr = get_audio_data(out)

                arxs.set_audio_data(data)
                arxs.set_sampling_rate(sr)

                # arxs.set_text_attribute('source', '')
                arxs.set_text_attribute('signal_type', arxs.get_signal_type())
                # arxs.set_text_attribute('name', '')
                arxs.set_text_attribute('d_type', str(type(data)))
                arxs.set_text_attribute('fs_path', out)
                arxs.set_text_attribute('channels', data.shape[1])
                arxs.set_text_attribute('shape', data.shape)
                arxs.set_text_attribute('sr', sr)

                # print(f'arxs:\n{arxs.get()}')

                # import asyncio
                from src.arx.lib.ARXMQConsumer import ARXMQConsumer
                consumer = ARXMQConsumer()
                consumer.configure('arx.json')
                # loop = asyncio.get_event_loop()
                # loop.run_until_complete(consumer.consume())
                consumer.consume()

                # try:
                #     consumer = ARXMQConsumer()
                #     consumer.configure('arx.json')
                #     # loop = asyncio.get_event_loop()
                #     # loop.run_until_complete(consumer.consume())
                #     consumer.consume()
                #
                # except Exception as e:
                #     print(f'controller consumer failed : {e}')
                #     pass

                from src.arx.lib.ARXMQProvider import ARXMQProvider
                try:
                    provider = ARXMQProvider()
                    provider.configure('arx.json')
                    # loop = asyncio.get_event_loop()
                    # loop.run_until_complete(provider.send_sgnlpt(arxs)) #  RuntimeWarning: coroutine 'ZeroMQAsyncProducer.send_data' was never awaited
                    provider.send_sgnlpt(arxs)
                    pass
                except Exception as e:
                    print(f'controller producer failed : {e}')
                    pass

                metadata = consumer.get_metadata()     # potentially array, a Signal() or LIST of type
                print(f'metadata :{metadata}')
                audio_data = consumer.get_data()       # potentially array, a Signal() or LIST of type
                print(f'audio_data :{audio_data}')

                # message = consumer.get_message()       # potentially array, a Signal() or LIST of type
                # print(f'message :{message}')

            atexit.register(stop)

            if __name__ == '__main__':
                RESTServer(self.create_app()).run()
            routes.arxRec.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    ARXController().run()
