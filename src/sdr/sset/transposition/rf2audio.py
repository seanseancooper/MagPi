#  Copyright (c) 2025 Sean D. Cooper
#
#  This source code is licensed under the MIT license found in the LICENSE file in the root directory of this source tree.
#

import queue
import sys
import threading
import ffmpeg
import sounddevice as sd
import soundfile as sf


class rf_to_audio:
    """ Convert I/Q samples to WAV for human listening. """

    def __init__(self, filename, buffersize=20, blocksize=2048, device=0):

        self.filename = filename
        self.buffersize = buffersize
        self.blocksize = blocksize
        self.device = device

        self.samplerate = 44100
        self.channels = 2

        self.url = None

        self.q = queue.Queue(maxsize=self.buffersize)
        self.event = threading.Event()


    @staticmethod
    def int_or_str(text):
        """Helper function for argument parsing."""
        try:
            return int(text)
        except ValueError:
            return text

    def config(self):

        if self.blocksize == 0:
            print('blocksize must not be zero')
        if self.buffersize < 1:
            print('buffersize must be at least 1')


    def callback(self, outdata, frames, time, status):
        assert frames == self.blocksize

        if status.output_underflow:
            print('Output underflow: increase blocksize?', file=sys.stderr)
            raise sd.CallbackAbort
        assert not status
        try:
            data = self.q.get_nowait()
        except queue.Empty as e:
            print('Buffer is empty: increase buffersize?', file=sys.stderr)
            raise sd.CallbackAbort from e

        if len(data) < len(outdata):
            outdata[:len(data)] = data
            outdata[len(data):].fill(0)
            raise sd.CallbackStop
        else:
            outdata[:] = data

    def render(self):

        try:

            with sf.SoundFile(self.filename) as f:
                for _ in range(self.buffersize):
                    data = f.read(self.blocksize)
                    if not len(data):
                        break
                    self.q.put_nowait(data) # Pre-fill queue

                stream = sd.OutputStream(
                    samplerate=f.samplerate, blocksize=self.blocksize,
                    device=self.device, channels=f.channels,
                    callback=self.callback, finished_callback=self.event.set)

                with stream:

                    timeout = self.blocksize * self.buffersize / f.samplerate

                    while len(data):
                        data = f.read(self.blocksize)
                        self.q.put(data, timeout=timeout)
                    self.event.wait() # Wait until playback is finished

        except KeyboardInterrupt:
            print('Interrupted by user')
        except queue.Full:
            # A timeout occurred, i.e. there was an error in the callback
            exit(1)
        except Exception as e:
            exit(type(e).__name__ + ': ' + str(e))

    def render_stream(self):

        try:
            print('Opening stream ...')
            from ffmpeg import input, output

            process = input(
                    self.url
            ).output(
                    'pipe:',
                    format='f32le',
                    acodec='pcm_f32le',
                    ac=self.channels,
                    ar=self.samplerate,
                    loglevel='quiet',
            ).run_async(pipe_stdout=True)

            stream = sd.RawOutputStream(
                    samplerate=self.samplerate,
                    blocksize=self.blocksize,
                    device=self.device,
                    channels=self.channels,
                    dtype='float32',

                    callback=self.callback)
            read_size = self.blocksize * self.channels * stream.samplesize
            print('Buffering ...')
            for _ in range(self.buffersize):
                self.q.put_nowait(process.stdout.read(read_size))
                print('Starting Playback ...')
            with stream:
                timeout = self.blocksize * self.buffersize / self.samplerate
                while True:
                    self.q.put(process.stdout.read(read_size), timeout=timeout)
        except KeyboardInterrupt:
            print('\nInterrupted by user')
        except queue.Full:
            # A timeout occurred, i.e. there was an error in the callback
            exit(1)
        except Exception as e:
            exit(type(e).__name__ + ': ' + str(e))