import logging
from src.config import readConfig
import requests

from src.net.zeroMQ.ZeroMQAsyncConsumer import ZeroMQAsyncConsumer
from src.net.zeroMQ.ZeroMQAsyncProducer import ZeroMQAsyncProducer

logger_root = logging.getLogger('root_logger')
net_logger = logging.getLogger('net_logger')

def get_retriever(name):
    logger_root.debug(f'attempting to load retriever {name}')
    try:
        components = name.split('.')
        mod = __import__(components[0])
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod
    except AttributeError as a:
        logger_root.fatal(f'Failed to load retriever {name} {a}')
        exit(1)

def check_rmq_available(module):

    config = {}
    readConfig('net.json', config)

    rmq_username = config['RMQ_USERNAME']
    rmq_password = config['RMQ_PASSWORD']
    rmq_host = config['RMQ_HOST']
    rmq_port = config['RMQ_PORT']

    RMQ_AVAILABLE = True
    module_queue = f'{module}_queue'

    try:
        req = requests.get(f'http://{rmq_host}:{rmq_port}/api/queues', auth=(rmq_username, rmq_password))

        if req.ok:  # check for auth fail too!!
            # parse json response for queues "running"
            queues = req.json()
            for i, q in enumerate(queues):
                queue = queues[i]
                if queue['name'] == module_queue and queue['state'] != "running":
                    RMQ_AVAILABLE = False
                    net_logger.debug(f'NET::RMQ {module_queue} not available: queue not running.')
        else:
            RMQ_AVAILABLE = False
            net_logger.debug(f'NET::RMQ {module_queue} not available: healthcheck failed.')
    except Exception as e:
        RMQ_AVAILABLE = False
        net_logger.debug(f'Error: NET::RMQ {module_queue} is not available: {e}')

    return module, RMQ_AVAILABLE

def check_zmq_available():

    config = {}
    readConfig('net.json', config)
    ZMQ_AVAILABLE = True

    try:
        producer = ZeroMQAsyncProducer()
        arxs = producer.test()
        try:
            metadata = arxs.get_text_attributes()
            data = arxs.get_audio_data()

            import asyncio
            asyncio.run(producer.send_data(metadata, data))

            # loop = asyncio.get_event_loop()
            # loop.run_until_complete(producer.send_data(metadata, data))

        except Exception:
            ZMQ_AVAILABLE = False
            net_logger.debug(f'NET::ZMQ not available: healthcheck failed.')

    except Exception as e:
        ZMQ_AVAILABLE = False
        net_logger.info(f'Error: NET::ZMQ is not available: {e}')

    return None, ZMQ_AVAILABLE

def check_imq_available():
    """ IMQ uses ZMQ internally """

    try:
        return True
    except Exception as e:
        net_logger.debug(f'Error: NET::IMQ is not available: {e}')

if __name__ == '__main__':
    print(check_zmq_available())

    # consumer = ZeroMQAsyncConsumer()
    # consumer.run()

