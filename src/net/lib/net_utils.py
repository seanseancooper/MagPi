import logging

logger_root = logging.getLogger('root_logger')

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
    # this is an intentionally naive check; it fails if rabbit is
    # 'off', exposes passwords and... is not the focus.

    from src.config import readConfig

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
                    print(f'{module_queue} not available: queue not running.')
        else:
            RMQ_AVAILABLE = False
            print(f'{module_queue} not available: healthcheck failed.')
    except Exception as e:
        RMQ_AVAILABLE = False
        print(f'Error: {module_queue} is not available: {e}')

    return module, RMQ_AVAILABLE
