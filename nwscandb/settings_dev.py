# -*- coding: utf-8 -*-

DEBUG = True
TEMPLATE_DEBUG = True

DATABASES = None  # defined in secret settings

# import settings_dev_secret.py and take sensitive values (e.g. passwords) from there
from nwscandb.settings_basic import *
from nwscandb.settings_dev_secret import *


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/nwscandb_dev.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'nwscandb': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'dbimport': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'multidns': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'nmap': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
        'accounts': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    }
}
