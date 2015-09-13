import os
from nmapui.config import *
basedir = os.path.abspath(os.path.dirname(__file__))

BROKER_URL = "amqp://guest:guest@localhost:5672//"
CELERY_IMPORTS = ("nmapui.tasks", )
CELERY_ENABLE_UTC = True

CELERY_RESULT_BACKEND = "db+" + DATABASE_URI

CELERY_TIMEZONE = 'Europe/Berlin'

