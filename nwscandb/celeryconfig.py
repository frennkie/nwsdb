import datetime
from celery.schedules import crontab
from nwscandb.config import *
basedir = os.path.abspath(os.path.dirname(__file__))

BROKER_URL = "amqp://guest:guest@localhost:5672//"
CELERY_IMPORTS = ("nwscandb.tasks", )
CELERY_ENABLE_UTC = True

CELERY_RESULT_BACKEND = "db+" + DATABASE_URI

CELERY_TIMEZONE = 'Europe/Berlin'

# expire tasks that have not been executed yet
CELERY_TASK_EXPIRES = datetime.timedelta(days=5)

# 5-7 days might make sense here
CELERY_TASK_RESULT_EXPIRES = datetime.timedelta(days=1)

# enabling/scheduling BEAT is required for mysql backend
# nwscandb.tasks.CleanupTask might be redundant?!
CELERYBEAT_SCHEDULE = {
    # Executes every day at 3:30 (local)
    'add-every-morning': {
        'task': 'nwscandb.tasks.CleanupTask',
        'schedule': crontab(hour=4, minute=30),
    },
}

