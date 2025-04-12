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

                out = routes.arxRec.stop()  # required.
                # print(f'out: {out}')
                import soundfile as sf
                def get_audio_data(f):
                    return sf.read(f)

                from src.arx.lib.ARXSignalPoint import ARXSignalPoint
                arxs = ARXSignalPoint(routes.arxRec.get_worker_id(),
                                          routes.arxRec.lon,
                                          routes.arxRec.lat,
                                          routes.arxRec.signal_cache[:-1],
                                          )

                data, sr = get_audio_data(out)
                # print(f'data: {data}')
                arxs.set_audio_data(data)
                # print(f'ad: {arxs.get_audio_data()}')
                arxs.set_sampling_rate(sr)
                arxs.set_text_attribute('shape', data.shape)
                # print(arxs.get())
                # print(arxs.arxs_to_dict(arxs))

                from src.arx.lib.ARXMQProvider import ARXMQProvider
                try:
                    mq = ARXMQProvider()
                    mq.configure('arx.json')
                    loop = asyncio.get_event_loop()

                    loop.run_until_complete(mq.send_sgnlpt(arxs))
                except Exception as e:
                    print(f'mq failed : {e}')
                    pass

            atexit.register(stop)

            if __name__ == '__main__':
                RESTServer(self.create_app()).run()
            routes.arxRec.run()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    ARXController().run()
