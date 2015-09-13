import getpass
import bcrypt
from flask.ext.script import Manager, Server
from flask.ext.migrate import Migrate, MigrateCommand
from nmapui import app
from nmapui import db
from nmapui.models import Users, User
from nmapui.config import SQLALCHEMY_DATABASE_URI

manager = Manager(app)

manager.add_command("runserver", Server(use_debugger = True,
                                        use_reloader = True,
                                        host = '0.0.0.0', port=80))

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

@manager.command
def adduser(username, email):
    __p1 = getpass.getpass()
    __p2 = getpass.getpass("Confirm password:")
    if __p1 == __p2 and len(__p1):
        __px = bcrypt.hashpw(__p1 + app.config["PEPPER"], bcrypt.gensalt())
        u = Users.add(username=username, email=email, password=__px)
    else:
        print "Error: passwords do not match"

@manager.command
def create_db():
    """ needed?! """
    db.create_all()

if __name__ == "__main__":
    manager.run()

