# coding=utf-8
import logging
import logging.config
from logging import StreamHandler


def init_logging():
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'generic': {
                'format': '%(asctime)s [%(process)d] [%(levelname)s] %(name)s: %(message)s',  # noqa
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'generic',
            },
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': True,
            },
        }
    })

init_logging()
logger = logging.getLogger('peewee_cache')
logger.setLevel(logging.DEBUG)
s = StreamHandler()
fmt = logging.Formatter('%(asctime)s [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)s] %(name)s: %(message)s')
s.setFormatter(fmt)
logger.addHandler(s)
