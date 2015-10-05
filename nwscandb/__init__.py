__author__ = 'Robert Habermann'
__email__ =  'mail@rhab.de'
__license__ = 'CC-BY'
__version__ = '0.1.1'

# Initial code base CC-by Ronald Bister (mini.pelle@gmail.com)

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from itsdangerous import URLSafeTimedSerializer
from momentjs import momentjs
from nwscandb import config

app = Flask(__name__)
app.config.from_object(config)

db = SQLAlchemy(app)

login_serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.init_app(app)
login_manager.login_view = "ui.login"

from nwscandb.views import ui
from nwscandb.views import admin
from nwscandb.views import nmap
app.register_blueprint(ui.appmodule)
app.register_blueprint(admin.appmodule)
app.register_blueprint(nmap.appmodule)

# Set jinja template global
app.jinja_env.globals['momentjs'] = momentjs
app.jinja_env.add_extension('jinja2.ext.do')

if __name__ == '__main__':
    app.run()
