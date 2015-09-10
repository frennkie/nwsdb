import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = '973fb5503d479a2ccd1ce8b4227bdd3c'

REMEMBER_COOKIE_DURATION = timedelta(days=1)

# mongodb config
MONGO_DBNAME = 'nmapuidb'
MONGO_HOST = '127.0.0.1'
MONGO_PORT = 27017
MONGO_USERNAME = ''
MONGO_PASSWORD = ''

# File upload config
UPLOAD_FOLDER = basedir + 'nmapui/uploads'
ALLOWED_EXTENSIONS= set(['xml'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# nmap-webgui specific config variables
ROLE_USER = 2
ROLE_ADMIN = 4
