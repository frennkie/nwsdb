import getpass
from flask.ext.script import Manager, Server
from flask.ext.migrate import Migrate, MigrateCommand
from flask import Blueprint
from nwscandb import app
from nwscandb import db
from nwscandb.models import Users, UserGroup


manager = Manager(app)

manager.add_command("runserver", Server(use_debugger=True,
                                        use_reloader=True,
                                        host='0.0.0.0', port=80))

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def add_admin(username, email):
    """Create a admin user interactively

    This function creates an admin account and adds the account to the "admin"
    group. If this group does not yet exist (with id==1) it will also be created.
    During the creation the user will be prompted to enter a password twice.

    Args:
        username (str): Username
        email (str): E-Mail Address

    Returns:
        True or False as the result of creating the admin user

    """

    _admin_group = UserGroup.query.first()
    if _admin_group is None:
        try:
            _admin_group = UserGroup.add(id=1, name="admin", comment="Admin Group (1)")
        except Exception as e:
            print("Failed to add \"admin\" group: " + str(e)) # TODO print
            return False
    elif _admin_group.name != "admin":
        return False
    else:
        pass

    # create user and add to admin group
    add_user(username, _admin_group.name, email)
    db.session.commit()
    return True


@manager.command
def add_user(username, user_group_name, email):
    """Create a user"""
    __p1 = getpass.getpass()
    __p2 = getpass.getpass("Confirm password:")
    if __p1 == __p2 and len(__p1):
        return Users.add(username=username,
                         user_group_name=user_group_name,
                         email=email,
                         clear_pw=__p1)
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


def get_list_of_routes():
    rules = []
    for rule in app.url_map.iter_rules():
        rules.append(rule.rule)
    return rules


def get_list_of_endpoints():
    endpoints = []
    for rule in app.url_map.iter_rules():
        endpoints.append(rule.endpoint)
    return endpoints




if __name__ == "__main__":

    #print(get_list_of_routes())
    #print(get_list_of_endpoints())
    # now call a function that adds all endpoints to the admin user

    manager.run()

