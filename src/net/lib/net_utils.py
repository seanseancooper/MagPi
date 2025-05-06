import logging
from src.config import readConfig

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
        import requests
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
        import requests
        # # look for uRL
        # req = requests.get(f'http://{zmq_host}:{zmq_port}', auth=(zmq_username, zmq_password))
        #
        # if req.ok:  # check for auth fail too!!
        #     # process response
        #     pass
        # else:
        #     ZMQ_AVAILABLE = False
        #     net_logger.debug(f'NET::ZMQ not available: healthcheck failed.')
    except Exception as e:
        ZMQ_AVAILABLE = False
        net_logger.info(f'Error: NET::ZMQ is not available: {e}')

    return ZMQ_AVAILABLE

def check_imq_available():

    config = {}
    readConfig('net.json', config)

    IMQ_AVAILABLE = True

    try:
        import requests
        # # look for uRL
        # req = requests.get(f'http://{imq_host}:{imq_port}', auth=(imq_username, imq_password))
        #
        # if req.ok:  # check for auth fail too!!
        #     # process response
        #     pass
        # else:
        #     IMQ_AVAILABLE = False
        #     net_logger.debug(f'NET::IMQ not available: healthcheck failed.')
    except Exception as e:
        IMQ_AVAILABLE = False
        net_logger.debug(f'Error: NET::IMQ is not available: {e}')

    return IMQ_AVAILABLE
