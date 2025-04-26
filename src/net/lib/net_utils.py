

import logging


logger_root = logging.getLogger('root')
net_logger = logging.getLogger('net_logger')
speech_logger = logging.getLogger('speech_logger')


def get_retriever(name):
    try:
        components = name.split('.')
        mod = __import__(components[0])
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod
    except AttributeError as a:
        logger_root.fatal(f'Failed to load retriever {name} {a}')
        exit(1)
