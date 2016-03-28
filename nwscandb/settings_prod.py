# -*- coding: utf-8 -*-

DEBUG = False

WSGI_APPLICATION = 'nwscandb.wsgi_prod.application'

DATABASES = None  # defined in secret settings

# import settings_prod_secret.py and take sensitive values (e.g. passwords) from there
from nwscandb.settings_basic import *
from nwscandb.settings_prod_secret import *

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
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/nwscandb_prod.log',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'INFO',
        },
        'nwscandb': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        'dbimport': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        'multidns': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        'nmap': {
            'handlers': ['file'],
            'level': 'INFO',
        },
        'accounts': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    }
}
