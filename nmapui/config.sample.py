import os
from datetime import timedelta
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = '<fill_me>'
PEPPER = "<fill_me>"

REMEMBER_COOKIE_DURATION = timedelta(days=30)

# SQLAlchemy
#SQLALCHEMY_ECHO = True
SQLALCHEMY_ECHO = False

# MySQL
MYSQL_DB_USERNAME = 'nmap'
MYSQL_DB_PASSWORD = '<fill_me>'
MYSQL_DB_NAME = 'nmap'
MYSQL_DB_HOST = 'localhost'

DATABASE_URI = "mysql://{DB_USER}:{DB_PASS}@{DB_ADDR}/{DB_NAME}".format(DB_USER=MYSQL_DB_USERNAME,
                                                                        DB_PASS=MYSQL_DB_PASSWORD,
                                                                        DB_ADDR=MYSQL_DB_HOST,
                                                                        DB_NAME=MYSQL_DB_NAME)

SQLALCHEMY_DATABASE_URI = "mysql+py" + DATABASE_URI
LIBNMAP_DB_URI = DATABASE_URI

# File upload config
UPLOAD_FOLDER = basedir + 'nmapui/uploads'
ALLOWED_EXTENSIONS= set(['xml'])
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# nmap-webgui specific config variables
ROLE_USER = 2
ROLE_ADMIN = 4
