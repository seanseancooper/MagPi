import threading
import time
import matplotlib
import numpy as np

matplotlib.use('Agg')

from flask import Flask, Response, render_template
from flask_socketio import SocketIO, emit
from src.sdr.lib import SDRAnalyzer
from src.config import readConfig

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # <- ensure this matches your front-end host

class FlaskSDRStreamer:

    def __init__(self):

        global app
        self.app = app

        self.host = None
        self.port = None
        self.config = {}
        self.configure('sdr.json')
        self.analyzer = SDRAnalyzer()
        self.setup_routes()
        self.debug = False

    def configure(self, config_file):
        readConfig(config_file, self.config)
        host, port = self.config['SERVER_NAME'].split(':')
        self.host = host
        self.port = int(port) + 10

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html.j2')

        @self.app.route('/spectrogram_stream')
        def spectrogram_stream():
            def generate():
                while True:
                    try:
                        buf = self.analyzer.render_spectrogram_jpg()
                        yield (
                            b"--pngboundary\r\n"
                            b"Content-Type: image/jpeg\r\n"
                            b"Content-Length: " + f"{len(buf.getvalue())}".encode() + b"\r\n\r\n" +
                            buf.getvalue() + b"\r\n"
                        )
                        time.sleep(0.01)  # adjust to control frame rate
                    except Exception as e:
                        print(f"Stream error: {e}")
                        break

            headers = {
                'Cache-Control': 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0',
                'Pragma': 'no-cache'
            }
            return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=pngboundary', headers=headers)

        @socketio.on('extract_signal')
        def handle_extract(data):
            center_freq = data['center_freq']
            bandwidth = data['bandwidth']
            start_time = data['start_time']
            end_time = data['end_time']

            signal = self.analyzer.extract_signal(center_freq, bandwidth, start_time, end_time)
            emit('signal_extracted', {
                'status': 'done',
                'num_samples': len(signal),
                'sample_rate': self.analyzer.sample_rate
            })

        @socketio.on('read_block')
        def read_block():
            data = self.analyzer.reader.read_block()
            block = self.analyzer.generate_spectrogram_row(data)

            if block is not None:
                emit('block_data', block.astype(np.float32).tobytes())
                # emit('block_data', block.tobytes())
            else:
                emit('block_data', [])  # or handle error case

    # def start_streaming_loop(self):
    #     def update_loop():
    #         while True:
    #             try:
    #                 self.analyzer.update_loop()
    #                 # time.sleep(0.01)
    #             except Exception as e:
    #                 print(f"Update loop error: {e}")
    #                 break
    #     threading.Thread(target=update_loop, daemon=True).start()

    def run(self):
        # self.start_streaming_loop()
        socketio.run(self.app, host=self.host, port=self.port, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    app = FlaskSDRStreamer()
    print('FlaskSDRStreamer')
    app.run()
