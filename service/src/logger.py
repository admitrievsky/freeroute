import logging
import sys

from config import get_config


def init_logging():
    for logger_name, level in get_config().loggers.items():
        logging.getLogger(logger_name).setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        logging.getLogger(logger_name).addHandler(handler)


logger = logging.getLogger('freeroute')
