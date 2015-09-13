import bcrypt
import datetime
from flask.ext.login import UserMixin
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine, MetaData, Table, desc
from libnmap.parser import NmapParser, NmapParserException
from bson.objectid import ObjectId
from nmapui import app
from nmapui import db
from nmapui import login_serializer
from nmapui.celeryapp import celery_pipe

# move to __init__.py ?!
engine = create_engine(app.config["DATABASE_URI"], convert_unicode=True)
metadata = MetaData(bind=engine)
celery_taskmeta = Table('celery_taskmeta', metadata, autoload=True)
nmap_task = Table('nmap_task', metadata, autoload=True)

class Users(object):
    """ """

    @classmethod
    def find(cls, **kwargs):
        """ find Users from database
        Args:
            cls (Class):
            **kwargs: Optional

        Returns:
            List of User objects

        Examples:
            TODO

        """
        _users = []
        _dbusers = User.query.filter_by(**kwargs)
        for _dbuser in _dbusers:
            _users.append(User(id=_dbuser.id,
                          username=_dbuser.username,
                          password=_dbuser.password,
                          email=_dbuser.email))
        return _users

    @classmethod
    def get(cls, user_id):
        """ """
        _user = None
        _dbuser = User.query.get(user_id)
        _user = User(id=_dbuser.id,
                     username=_dbuser.username,
                     password=_dbuser.password,
                     email=_dbuser.email)
        return _user

    @classmethod
    def add(cls, username=None, email=None, password=None):
        """ """
        rval = False
        if username is not None and email is not None and password is not None:
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            rval = True
        return rval


class User(db.Model, UserMixin):
    """ User Class and SQL Table """
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password = db.Column(db.String(128))
    email = db.Column(db.String(128))

    def __init__(self, id=None, username=None, email=None, password=None):
        self.id = id
        self.username = username
        self.password = password
        self.email = email

    def get_auth_token(self):
        """
        Encode a secure token for cookie
        """
        data = [str(self.id), self.password]
        return login_serializer.dumps(data)

    def credentials_valid(self, _password):
        _db_password_utf8 = self.password.encode('utf-8')
        return bcrypt.hashpw(_password.encode('utf-8') + app.config["PEPPER"],
                             _db_password_utf8) == _db_password_utf8

    def __repr__(self):
        return "<User {0}> ({1})".format(self.username, self.email)


class NmapTask(db.Model):
    """ NmapTask Class """
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(128))
    task_id = db.Column(db.String(36))
    created = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship('User', backref='nmaptask')

    def __init__(self, id=None, comment=None, task_id=None, user_id=None,
                 created=datetime.datetime.utcnow()):
        self.id = id
        self.comment = comment
        self.task_id = task_id
        self.user_id = user_id
        self.created = created


    @classmethod
    def find(cls, asc=True, **kwargs):
        _reports = []

        if asc is True:
            _dbreports = NmapTask.query.filter_by(**kwargs).order_by("id")
        else:
            _dbreports = NmapTask.query.filter_by(**kwargs).order_by(desc("id"))


        for _dbreport in _dbreports:
            _nmap_task = {'task_id': celery_pipe.AsyncResult(_dbreport.task_id),
                          'comment': _dbreport.comment,
                          'created': _dbreport.created}
            _reports.append(_nmap_task)
        return _reports


    @classmethod
    def get(cls, task_id):
        #print("DEBUG: nmaptask_get: " + str(task_id))
        _report = None
        if isinstance(task_id, str) or isinstance(task_id, unicode):
            try:
                _resultdict = celery_pipe.AsyncResult(task_id).result
            except NmapParserException:
                pass
        #print("DEBUG: nmaptask_get resultdict: " + str(_resultdict))
        return _resultdict

    @classmethod
    def get_report(cls, task_id):
        #print("DEBUG: nmaptask_getreport: " + task_id)
        _report = None
        if isinstance(task_id, str) or isinstance(task_id, unicode):
            try:
                _resultdict = celery_pipe.AsyncResult(task_id).result
                _resultxml = _resultdict['report']
                _report = NmapParser.parse_fromstring(_resultxml)
            except NmapParserException:
                pass
        return _report

    @classmethod
    def add(cls, user_id=None, task_id=None, comment=None):
        rval = False
        if user_id is not None and task_id is not None and comment is not None:
            new_nmaptask = NmapTask(user_id=user_id, task_id=task_id,
                                    comment=comment)
            db.session.add(new_nmaptask)
            db.session.commit()
            rval = True
        return rval

    @classmethod
    def remove_task_by_id(cls, task_id=task_id):
        """  """
        result = False

        if task_id is not None:
            con = engine.connect()
            result = con.execute(celery_taskmeta.delete().where(celery_taskmeta.c.task_id == task_id))
            if result.rowcount != 1:
                print "celery_taskmeta: Something is wrong... should have found exactly one row"
            result = con.execute(nmap_task.delete().where(nmap_task.c.task_id == task_id))
            if result.rowcount != 1:
                print "nmap_task: Something is wrong... should have found exactly one row"
            con.close()

            result = True
        return result


class NmapDiffer(object):
    """Foo"""

    def __init__(self, old_report=None, new_report=None):
        self.changed = []
        self.added = []
        self.removed = []
        print old_report
        if old_report and new_report:
            print "using given old and new_report"
            #pass
        else:
            print "no valid data.. taking dummy files from disk"
            old_report = NmapParser.parse_fromfile('nmapui/test/1_hosts.xml')
            new_report = NmapParser.parse_fromfile('nmapui/test/1_hosts_diff.xml')

        self.do_diff(new_report, old_report)
        self.print_diff()

    def print_diff(self):
        """output for debug """
        print self.changed
        print self.added
        print self.removed

    def do_diff(self, obj1, obj2):
        ndiff = obj1.diff(obj2)

        self.do_diff_changed(obj1, obj2, ndiff.changed())
        self.do_diff_added(obj1, obj2, ndiff.added())
        self.do_diff_removed(obj1, obj2, ndiff.removed())

    def nested_obj(self, objname):
        rval = None
        splitted = objname.split("::")
        if len(splitted) == 2:
            rval = splitted
        return rval


    def do_diff_added(self, obj1, obj2, added):
        for akey in added:
            nested = self.nested_obj(akey)
            if nested is not None:
                if nested[0] == 'NmapHost':
                    subobj1 = obj1.get_host_byid(nested[1])
                elif nested[0] == 'NmapService':
                    subobj1 = obj1.get_service_byid(nested[1])
                self.added.append("+ {0}".format(subobj1))
            else:
                self.added.append("+ {0} {1}: {2}".format(obj1, akey, getattr(obj1, akey)))

    def do_diff_removed(self, obj1, obj2, removed):
        for rkey in removed:
            nested = self.nested_obj(rkey)
            if nested is not None:
                if nested[0] == 'NmapHost':
                    subobj2 = obj2.get_host_byid(nested[1])
                elif nested[0] == 'NmapService':
                    subobj2 = obj2.get_service_byid(nested[1])
                self.removed.append("- {0}".format(subobj2))
            else:
                self.removed.append("- {0} {1}: {2}".format(obj2, rkey, getattr(obj2, rkey)))

    def do_diff_changed(self, obj1, obj2, changed):
        for mkey in changed:
            nested = self.nested_obj(mkey)
            if nested is not None:
                if nested[0] == 'NmapHost':
                    subobj1 = obj1.get_host_byid(nested[1])
                    subobj2 = obj2.get_host_byid(nested[1])
                elif nested[0] == 'NmapService':
                    subobj1 = obj1.get_service_byid(nested[1])
                    subobj2 = obj2.get_service_byid(nested[1])
                self.do_diff(subobj1, subobj2)
            else:
                self.changed.append("~ {0} {1}: {2} => {3}".format(obj1, mkey,
                                                    getattr(obj2, mkey),
                                                    getattr(obj1, mkey)))

