from celery import Celery
from nwscandb import celeryconfig

celery_pipe = Celery()
celery_pipe.config_from_object(celeryconfig)
