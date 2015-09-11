import getpass
import bcrypt
from flask.ext.script import Manager, Server
from nmapui import app
from nmapui.models import Users

manager = Manager(app)
manager.add_command("runserver", Server(use_debugger = True,
                                  use_reloader = True,
                                  host = '0.0.0.0', port=80))

@manager.command
#@manager.option('-u', '--username', help='your username')
#@manager.option('-e', '--email', help='your email address')
def adduser(username, email):
    rval = False
    __p1 = getpass.getpass()
    __p2 = getpass.getpass("Confirm password:")
    if __p1 == __p2 and len(__p1):
        __px = bcrypt.hashpw(__p1 + app.config["PEPPER"], bcrypt.gensalt())
        u = Users.add(username=username, email=email, password=__px)
    else:
        print "Error: password do not match"

if __name__ == "__main__":
    manager.run()
