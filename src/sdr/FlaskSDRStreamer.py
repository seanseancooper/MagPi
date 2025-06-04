import time
import threading
import matplotlib
matplotlib.use('Agg')

from flask import Flask, Response, render_template
from flask_socketio import SocketIO, emit
from src.sdr.lib import SDRAnalyzer
from src.config import readConfig

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # <- ensure this matches your front-end host

class FlaskSDRStreamer:

    def __init__(self, host='0.0.0.0', port=5000):
        global app
        self.app = app

        self.host = host
        self.port = port
        self.analyzer = SDRAnalyzer()
        self.setup_routes()
        self.config = {}
        self.debug = False

    def configure(self, config_file):
        readConfig(config_file, self.config)

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html.j2')

        @self.app.route('/spectrogram_stream')
        def spectrogram_stream():
            def generate():
                while True:
                    try:
                        buf = self.analyzer.render_spectrogram_png()
                        yield (
                            b"--pngboundary\r\n"
                            b"Content-Type: image/png\r\n"
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

    def start_streaming_loop(self):
        def update_loop():
            while True:
                try:
                    self.analyzer.update_loop()
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Update loop error: {e}")
                    break
        threading.Thread(target=update_loop, daemon=True).start()

    def run(self):
        self.start_streaming_loop()
        socketio.run(self.app, host=self.host, port=self.port, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    app = FlaskSDRStreamer()
    app.configure('sdr.json')
    print('FlaskSDRStreamer')
    app.run()
