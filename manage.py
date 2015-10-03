import getpass
import sys
import bcrypt
from flask.ext.script import Manager, Server
from flask.ext.migrate import Migrate, MigrateCommand
from nmapui import app
from nmapui import db
from nmapui.models import Users, User, Permission
from nmapui.config import SQLALCHEMY_DATABASE_URI

manager = Manager(app)

manager.add_command("runserver", Server(use_debugger = True,
                                        use_reloader = True,
                                        host = '0.0.0.0', port=80))

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

@manager.command
def add_admin(username, email):
    """Create an admin user"""
    _admin_permission = Permission.query.first()
    if _admin_permission is None:
        try:
            Permission.add(id=1, name="admin")
        except Exception as e:
            print("Failed to add \"admin\" permission: " + str(e))
            sys.exit()
    # create user (using function defined below)
    _u = add_user(username, email)
    # now add permission to newly created user
    _u.permissions.append(_admin_permission)
    db.session.commit()

@manager.command
def add_user(username, email):
    """Create a user"""
    __p1 = getpass.getpass()
    __p2 = getpass.getpass("Confirm password:")
    if __p1 == __p2 and len(__p1):
        __px = bcrypt.hashpw(__p1 + app.config["PEPPER"], bcrypt.gensalt())
        return Users.add(username=username, email=email, password=__px)
    else:
        print "Error: passwords do not match"

@manager.option("user_id", help="numeric User ID")
def change_password(user_id):
    """Change a user password"""
    try:
        _user = Users.get(user_id)
    except:
        print("Not User found for ID: " + str(user_id))

    print("Changing Password for User: " + _user.username)

    __p1 = getpass.getpass()
    __p2 = getpass.getpass("Confirm password:")
    if __p1 == __p2 and len(__p1):
        __px = bcrypt.hashpw(__p1 + app.config["PEPPER"], bcrypt.gensalt())
        _user.change_password(__px)
    else:
        print("Error: passwords do not match")

@manager.command
def create_db():
    """Create databases"""

    """ needed?!
    https://stackoverflow.com/questions/21482817/alembic-flask-migrate-doesnt-recognise-database-structure
    Do not call db.create_all() when you use Flask-Migrate/Alembic.
    The migration framework replaces that call.
    """
    db.create_all()

if __name__ == "__main__":
    manager.run()

