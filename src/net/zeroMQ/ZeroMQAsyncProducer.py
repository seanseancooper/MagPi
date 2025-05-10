import zmq
import json
import logging

net_logger = logging.getLogger('net_logger')

class ZeroMQAsyncProducer:
    """
    Publish ARXSignalPoint audio data to offline processing.
    ZeroMQ Producer: Produce a 'message' composed of:
            metadata: a mapping of 'text_attributes' sent [utf-8].
            data: byte array of data sent
    """
    def __init__(self):
        context = zmq.Context()

        self.socket = context.socket(zmq.PUSH)   #???!!!!!!
        self.socket.connect("tcp://127.0.0.1:5555")

    async def send_data(self, metadata, audiodata):
        message = json.dumps(metadata).encode('utf-8') + b'||' + audiodata.tobytes()
        net_logger.debug(f"Sending data. {metadata['id']}")
        self.socket.send(message)


    def test(self):

        from datetime import datetime
        import numpy as np

        from src.arx.lib.ARXSignalPoint import ARXSignalPoint
        from src.lib.utils import format_time

        arxs = ARXSignalPoint('00000-00000-000000',
                              0.0,
                              0.0,
                              0.0)

        data = np.zeros((1024, 2), dtype=np.float64)

        arxs.set_audio_data(data)
        arxs.set_sampling_rate(48000)

        arxs.set_text_attribute('signal_type', 'test')
        arxs.set_text_attribute('sent', format_time(datetime.now(), "%Y-%m-%d %H:%M:%S.%f"))
        arxs.set_text_attribute('fs_path', 'test')
        arxs.set_text_attribute('channels', data.shape[1])
        arxs.set_text_attribute('sr', 48000)
        arxs.set_text_attribute('frame_shape', data.shape)
        arxs.set_text_attribute('dtype', str(data.dtype))

        return arxs
        # while True:
        #     metadata = arxs.get_text_attributes()
        #     data = arxs.get_audio_data()
        #
        #     asyncio.run(producer.send_data(metadata, data))


if __name__ == "__main__":
    import asyncio
    producer = ZeroMQAsyncProducer()
    arxs = producer.test()

    while True:
        metadata = arxs.get_text_attributes()
        data = arxs.get_audio_data()

        asyncio.run(producer.send_data(metadata, data))
