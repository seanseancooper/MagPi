import unittest
from unittest.mock import patch, MagicMock
from src.arx.lib.ARXRecorder import ARXRecorder

from src.arx.lib.ARXRecorder import file_writing_thread


class TestARXRecorder(unittest.TestCase):

    @patch('src.arx.ARXRecorder.readConfig')
    @patch('src.arx.ARXRecorder.get_location')
    def test_configure(self, mock_get_location, mock_read_config):
        recorder = ARXRecorder()
        recorder.configure('dummy_config.json')
        mock_read_config.assert_called_once()
        mock_get_location.assert_called_once()

    def test_get_worker_id(self):
        recorder = ARXRecorder()
        self.assertEqual(recorder.get_worker_id(), 'ARXRecorder')

    def test_update_meter_empty_queue(self):
        recorder = ARXRecorder()
        result = recorder.update_meter()
        self.assertIn('peak_percentage', result)

    @patch('src.arx.ARXRecorder.sf.SoundFile')
    def test_file_writing_thread(self, mock_soundfile):
        mock_queue = MagicMock()
        mock_queue.get.side_effect = [b'test_data', None]
        file_writing_thread(q=mock_queue, file='dummy.wav', mode='w', samplerate=44100, channels=2)
        self.assertTrue(mock_soundfile.called)

    @patch('src.arx.ARXRecorder.sd.Stream')
    def test_create_stream(self, mock_stream):
        recorder = ARXRecorder()
        recorder.config = {
            'INPUT_DEVICE': 1,
            'OUTPUT_DEVICE': 2,
            'SR': 48000,
            'BLOCKSIZE': 1024,
            'DTYPE': 'float32',
            'LATENCY': 0.1,
            'CHANNELS': 2
        }
        recorder.create_stream()
        self.assertTrue(mock_stream.called)

    def test_stop_without_thread(self):
        recorder = ARXRecorder()
        recorder.thread = MagicMock()
        recorder.thread.is_alive.return_value = False
        recorder.thread.join = MagicMock()
        result = recorder.stop()
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
