import threading
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import numpy as np
import routes as routes

class SDRController(threading.Thread):

    def __init__(self):
        super().__init__()
        self.app = None
        self.socketio = None
        self.file_is_set = False

    def create_app(self):
        """Create Flask application."""
        self.app = Flask('sdr',
                    instance_relative_config=True,
                    subdomain_matching=True)

        CORS(self.app)
        self.app.config['CORS_HEADERS'] = 'Content-Type'

        self.socketio = SocketIO(self.app, cors_allowed_origins="*")  # <- ensure this matches front-end host
        socketio = self.socketio

        @socketio.on('extract_signal')
        def handle_extract(data):
            center_freq = routes.analyzer.center_freq
            bandwidth = data['bandwidth']
            start_time = data['start_time']
            end_time = data['end_time']

            signal = routes.analyzer.extract_signal(center_freq, bandwidth, start_time, end_time)
            emit('signal_extracted', {
                'status'     : 'done',
                'num_samples': len(signal),
                'sample_rate': routes.analyzer.sample_rate
            })

        def emits_block(data):
            block = routes.analyzer.get_magnitudes(data)
            if block is not None:
                emit('block_data', block.astype(np.float32).tobytes())
            else:
                emit('block_data', [])  # or handle error case

        @socketio.on('read_block')
        def read_block():
            if self.file_is_set:
                data = routes.analyzer.reader.read_block()
            else:
                # data = routes.scanner.module_retriever.block.copy() # read directly from hardware unbuffered.
                data = routes.scanner.scanned[0]                      # use buffered data from Scanner.
            emits_block(data)

        @socketio.on('read_blank')
        def read_blank():
            emits_block(np.zeros((routes.scanner.config['NFFT']*4,), dtype=np.complex128))

        @socketio.on('get_peaks')
        def get_peaks():
            emit('peak_data', routes.analyzer.peaks.tolist())

        @socketio.on('set_freq')
        def set_freq(new_center_freq):
            emit('center_freq', routes.scanner.module_retriever.set_center_freq(new_center_freq))

        @socketio.on('set_file')
        def set_file(fileName):

            routes.analyzer.reader.set_path(fileName)
            routes.analyzer.reader.load_file(fileName)  # point analyzer @filename one time
            self.file_is_set = True
            emit('set_file')

        @socketio.on('get_time')
        def get_time():
            ms = routes.scanner.elapsed.microseconds
            emit('get_time', ms * 100)

        @socketio.on('meta_data')
        def get_meta_data():
            meta_data = {  # fake data!!!
                "id"         : 42,
                "start_time" : "2025-06-01T14:00:00Z",
                "end_time"   : "2025-06-01T14:00:05Z",
                "center_freq": 98.5e6,
                "bandwidth"  : 200e3,
                "modulation" : "FM",
                "snr"        : 27.4,
                "label"      : "Weather Broadcast",
            }

            emit('meta_data', meta_data)

        with self.app.app_context():
            if __name__ == '__main__':
                self.app.config['SERVER_NAME'] = routes.scanner.config['SERVER_NAME']
                self.app.config['DEBUG'] = routes.scanner.config['DEBUG']
                self.app.register_blueprint(routes.sdr_bp)
            return self.app

    def run(self) -> None:
        try:
            import atexit

            def stop():
                routes.scanner.stop()
            atexit.register(stop)

            self.app = self.create_app()
            host, port = routes.scanner.config['SERVER_NAME'].split(':')
            self.socketio.run(self.app, host=host, port=int(port), allow_unsafe_werkzeug=True)
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    SDRController().run()