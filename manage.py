import getpass
import sys
from flask.ext.script import Manager, Server
from flask.ext.migrate import Migrate, MigrateCommand
from nwscandb import app
from nwscandb import db
from nwscandb.models import Users, Permission


manager = Manager(app)

manager.add_command("runserver", Server(use_debugger=True,
                                        use_reloader=True,
                                        host='0.0.0.0', port=80))

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
        return Users.add(username=username, email=email, clear_pw=__p1)
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
        _user.change_password(clear_pw=__p1)
    else:
        print("Error: passwords do not match")


@manager.command
def create_db():
    """Create databases"""

    """ needed?!
    https://stackoverflow.com/questions/21482817/
    Do not call db.create_all() when you use Flask-Migrate/Alembic.
    The migration framework replaces that call.
    """
    db.create_all()

if __name__ == "__main__":
    manager.run()

