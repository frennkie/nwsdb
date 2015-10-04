import bcrypt
import datetime
import json
from flask.ext.login import UserMixin
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy_utils import IPAddressType
from sqlalchemy import asc, desc
from libnmap.parser import NmapParser, NmapParserException
from libnmap.plugins.backendpluginFactory import BackendPluginFactory

from bson.objectid import ObjectId
from nmapui import app
from nmapui import db
from nmapui import login_serializer
from nmapui.celeryapp import celery_pipe
from celery.task.control import revoke




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
            _users.append(User.query.get(_dbuser.id))
        return _users

    @classmethod
    def get(cls, user_id):
        """get excactly one user identified by ID"""

        _user = None
        _dbuser = User.query.get(user_id)
        _user = User.query.get(_dbuser.id)
        return _user

    @classmethod
    def add(cls, username=None, email=None, clear_pw=None):
        """add new user to database"""

        if not (username and email and clear_pw):
            print("Error: username, email and clear_pw are all mandatory.")
            raise Exception("Neither username, email nor clear_pw can be None.")

        if len(Users.find(username=username)) > 0:
            print("Error: username already in use.")
            raise ValueError("Username already in use.")
        else:

            new_user = User(username=username,
                            email=email,
                            clear_pw=clear_pw)
            db.session.add(new_user)
            db.session.commit()
            return new_user

""" permissions handles many-to-many relation of Permission and User Class """
permissions = db.Table('permissions',
    db.Column('permission_id', db.Integer, db.ForeignKey('permission.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model, UserMixin):
    """User Class and SQL Table"""
    __table_args__ = {'sqlite_autoincrement': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password = db.Column(db.String(128))
    email = db.Column(db.String(128))
    nmaptasks = db.relationship('NmapTask', backref=db.backref('buser'))
    permissions = db.relationship('Permission',
                                  secondary=permissions,
                                  lazy='dynamic',
                                  backref=db.backref('users', lazy='dynamic'))

    def __init__(self, id=None, username=None, email=None, clear_pw=None):
        self.id = id
        self.username = username
        _pw = bcrypt.hashpw(clear_pw + app.config["PEPPER"], bcrypt.gensalt())
        self.password = _pw
        self.email = email

    def __repr__(self):
        return "<{0}[{1}]: {2} ({3})>".format(self.__class__.__name__,
                                       self.id,
                                       self.username,
                                       self.email)

    def get_auth_token(self):
        """Encode a secure token for cookie"""
        data = [str(self.id), self.password]
        return login_serializer.dumps(data)

    def credentials_valid(self, _password):
        _db_password_utf8 = self.password.encode('utf-8')
        return bcrypt.hashpw(_password.encode('utf-8') + app.config["PEPPER"],
                             _db_password_utf8) == _db_password_utf8

    def change_password(self, clear_pw=None):
        _pw = bcrypt.hashpw(clear_pw + app.config["PEPPER"], bcrypt.gensalt())
        db.session.query(User).filter(User.id == self.id).update({'password': _pw})
        db.session.commit()

    def has_permission(self, name):
        """Check out whether a user has a permission or not."""
        permission = Permission.query.filter_by(name=name).first()
        # if the permission does not exist or was not given to the user
        if not permission or not permission in self.permissions:
            return False
        return True

    def grant_permission(self, name):
        """Grant a permission to a user."""
        permission = Permission.query.filter_by(name=name).first()
        if permission and permission in self.permissions:
            return
        if not permission:
            permission = Permission()
            permission.name = name
            db.session.add(permission)
            db.session.commit()
        self.permissions.append(permission)

    def revoke_permission(self, name):
        """Revoke a given permission for a user."""
        permission = Permission.query.filter_by(name=name).first()
        if not permission or not permission in self.permissions:
            return
        self.permissions.remove(permission)


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    comment = db.Column(db.String(128))

    def __init__(self, id=None, name=None, comment=None):
        self.id = id
        self.name = name
        self.comment = comment

    def __repr__(self):
        return "<{0} {1}: {2} ({3})>".format(self.__class__.__name__,
                                       self.id,
                                       self.name,
                                       self.comment)

    @classmethod
    def add(cls, id=None, name=None, comment=None):
        """Add new permission"""
        if name is None:
            print("name is required!")
            raise("name is required!")
        if id and name != "admin":
            print("Error: don't hardcode Permission IDs (except for admin).")
            raise Exception("Don't hardcode Permission IDs (except for admin).")

        _new_perm = Permission(id=id, name=name, comment=comment)
        db.session.add(_new_perm)
        db.session.commit()
        return _new_perm

    def delete(self):
        if self.name == "admin":
            raise Exception("Group \"admin\" can not be deleted.")

        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            print("Error: " + str(e))
            return False


class NmapTask(db.Model):
    """ NmapTask Class """
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(36))
    comment = db.Column(db.String(128))
    created = db.Column(db.DateTime)
    completed = db.Column(db.SmallInteger)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, id=None, comment=None, task_id=None, user=None,
                 created=None, completed=0):
        self.id = id
        self.comment = comment
        self.task_id = task_id
        self.user_id = user.id
        self.created = created
        self.completed = completed

    def __repr__(self):
        return "<{0} {1}: {2}>".format(self.__class__.__name__,
                                       self.id,
                                       self.task_id)

    @classmethod
    def find(cls, sort_asc=True, **kwargs):
        _nmap_tasks = []

        if sort_asc is True:
            _db_nmap_tasks = NmapTask.query.filter_by(**kwargs).order_by(asc("id")).all()
        else:
            _db_nmap_tasks = NmapTask.query.filter_by(**kwargs).order_by(desc("id")).all()

        for _db_nmap_task in _db_nmap_tasks:

            async_result = celery_pipe.AsyncResult(_db_nmap_task.task_id)
            _db_nmap_task.async_result = async_result
            _nmap_tasks.append(_db_nmap_task)
        return _nmap_tasks


    @classmethod
    def get(cls, task_id):
        """TODO """
        #print("DEBUG: nmaptask_get: " + str(task_id))
        _report = None
        if isinstance(task_id, str) or isinstance(task_id, unicode):
            try:
                # TODO this shouldn't go look into AsyncResult.. or should it?
                _resultdict = celery_pipe.AsyncResult(task_id).result
            except NmapParserException as e:
                print e
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
            except NmapParserException as e:
                print e
        return _report

    @classmethod
    def add(cls, user=None, task_id=None, comment=None):
        """TODO"""
        if not (user and task_id):
            print("Error: user and task_id are all mandatory.")
            raise ValueError("Neither user nor task_id can be None.")
        try:
            _nmap_task = NmapTask(user=user,
                                  task_id=task_id,
                                  comment=comment,
                                  created=datetime.datetime.utcnow())
            db.session.merge(_nmap_task)
            db.session.commit()
            return _nmap_task
        except:
            print("Error: could not add scan task.")
            raise Exception("Could not add scan task.")


    @classmethod
    def remove_task_by_id(cls, task_id=task_id):
        """  """

        try:
            if task_id is not None:
                nt = NmapTask.query.filter(NmapTask.task_id == task_id).one()
                db.session.delete(nt)
                db.session.commit()
                return True
            else:
                return False

        except Exception as e:
            print("Error: " + str(e))
            return False

    @classmethod
    def stop_task_by_id(cls, task_id=task_id):
        """  """
        print("This is not implemented1")
        """
        print("trying to stop " + task_id)
        try:
            #revoke(task_id, terminate=True, signal="SIGUSR1")
            revoke(task_id, terminate=True)
            return True
        except Exception as e:
            print(e)
            return False
        """
        return False


class NmapReportDiffer(object):
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

    def __repr__(self):
        return "<{0}>".format(self.__class__.__name__)

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

""" --- """

class NmapReportMeta(db.Model):
    """ Meta Class for NmapReport

        This class needs to copy data from NmapTask Table that can (and will be
        removed from there.. therefore this can not be implemented as foreigen
        key..

    """

    id = db.Column(db.Integer, primary_key=True)
    # "foreign key"/identifier is the NmapTask.task_id (faef323-afec3-a...)
    task_task_id = db.Column(db.String(36))
    task_comment = db.Column(db.String(128))
    task_created = db.Column(db.DateTime)
    report_stored = db.Column(db.DateTime)
    report_id = db.Column(db.Integer)
    task_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


    def __init__(self, task_id=None):
        self.task_id = task_id
        # TODO .. id ..?! sql.. ? db.session.add(self) + commit()?


    def __repr__(self):
        return "<{0} {1}> TaskID: ({2}), UserID: {4}, Comment: ({3})".format(
                self.__class__.__name__,
                self.id,
                self.task_task_id,
                self.task_comment,
                self.task_user_id)

    @classmethod
    def get_report_meta(cls, **kwargs):
        """get one NmapReport"""

        #NmapReportMeta.query.filter_by(**kwargs).order_by("id")
        return NmapReportMeta.query.filter_by(**kwargs).order_by(asc("id")).all()

    @classmethod
    def get_report(cls, report_id):
        """get one NmapReport"""

        dbp = BackendPluginFactory.create(plugin_name='sql',
                                          url=app.config["LIBNMAP_DB_URI"],
                                          echo=False)
        return dbp.get(report_id=report_id)

    @classmethod
    def get_report_by_task_id(cls, report_id=None, task_id=None):
        """TODO will probably only need either report or task id"""
        pass

    @classmethod
    def getall_reports(cls):
        """getall NmapReport"""

        dbp = BackendPluginFactory.create(plugin_name='sql',
                                          url=app.config["LIBNMAP_DB_URI"],
                                          echo=False)
        return dbp.getall()

    def save_report(self, task_id=None):
        """ TODO """

        # TODO this is murks.. need to add a method to gets 1 NmapTask obj!
        _nmap_task_list = NmapTask.find(task_id=task_id)
        _nmap_task = _nmap_task_list[0]

        # mark nmap_task as done in table
        _nmap_task.completed = 1
        db.session.commit()
        #print(_nmap_task)

        _report = NmapTask.get_report(task_id=task_id)
        #print(_report)

        # save Meta information of Report
        self.task_task_id = _nmap_task.task_id
        self.task_comment = _nmap_task.comment
        self.task_created = _nmap_task.created
        self.task_user_id = _nmap_task.user_id
        self.report_stored = datetime.datetime.utcnow()

        try:
            dbp = BackendPluginFactory.create(plugin_name="sql",
                                              url=app.config["LIBNMAP_DB_URI"],
                                              echo=False)

            _id = _report.save(dbp)
            self.report_id = _id

            # call Address.discover which discovers and stores addresses
            r = Address.discover_from_report(report_id=_id)

            # save new NmapReportMeta instance to db
            db.session.add(self)
            db.session.commit()

            return {"rc": 0}

        except Exception as e:
            print e
            return {"rc": 1}

    def create_scan_from_report(self):
        pass


contacts = db.Table("contacts",
    db.Column('contact_id', db.Integer, db.ForeignKey('contact.id')),
    db.Column('address_detail_id', db.Integer, db.ForeignKey('address_detail.id'))
)

class AddressDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    name = db.Column(db.String(128))
    comment = db.Column(db.String(128))
    source = db.Column(db.String(128))
    ip_address = db.Column(IPAddressType)
    report_id = db.Column(db.Integer)
    contact = db.relationship("Contact", secondary=contacts)

    def __init__(self, id=None, created=datetime.datetime.utcnow(), name=None,
                 comment=None, source=None, ip_address=None, report_id=None):
        self.id = id
        self.created = created
        self.name = name
        self.comment = comment
        self.source = source
        self.ip_address = ip_address
        self.report_id = report_id

    def __repr__(self):
        return "<{0} {1}> ({5}) Name: ({3}) IP: {6}".format(
                self.__class__.__name__,
                self.id,
                self.created,
                self.name,
                self.comment,
                self.source,
                self.ip_address,
                self.report_id)


class Contact(db.Model):
    """ User Class and SQL Table """
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128))
    address_detail = db.relationship("AddressDetail", secondary=contacts)

    def __init__(self, id=None, created=datetime.datetime.utcnow(), name=None,
            email=None):
        self.id = id
        self.created = created
        self.name = name
        self.email = email

    def __repr__(self):
        return "<{0} {1}> Name: ({3}) Mail: ({4})".format(
                self.__class__.__name__,
                self.id,
                self.created,
                self.name,
                self.email)

class Address(object):
    """ Address class for modeling Scan Targets """

    def __init__(address=None):
        self.address = address

    def __repr__(self):
        return "<{0} {1}>".format(
                self.__class__.__name__,
                self.address)

    @classmethod
    def discover_from_report(cls, report_id):
        """discover hosts from report and store in db"""

        nmap_report = NmapReportMeta.get_report(report_id)

        if nmap_report:
            for host in nmap_report._hosts:
                #print("Address: " +  str(host.address) + " is: " + host.status)
                ad = AddressDetail(comment="scanned by me", source="nmap_scan",
                                   ip_address=host.address,
                                   report_id=report_id)
                db.session.add(ad)

            db.session.commit()
            return True

        else:
            print "could not extract report"
            return False


    @classmethod
    def discover_from_reports(cls):
        """ discover hosts """

        nmapreportList = NmapReportMeta.getall_reports()

        all_addresses = []
        for report_id, report_obj in nmapreportList:
            #print str(report_id) + ": " + str(report_obj)
            #print report_obj._hosts
            for host in report_obj._hosts:
                all_addresses.append({"address": host.address, "report_id": report_id})

        print "\n---\n"
        print all_addresses

#EOF
