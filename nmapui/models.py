import bcrypt
import datetime
import json
from flask.ext.login import UserMixin
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy_utils import IPAddressType
from libnmap.parser import NmapParser, NmapParserException
from libnmap.plugins.backendpluginFactory import BackendPluginFactory

from bson.objectid import ObjectId
from nmapui import app
from nmapui import db
from nmapui import login_serializer
from nmapui.celeryapp import celery_pipe




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
    nmaptasks = db.relationship('NmapTask', backref=db.backref('buser'))

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

    def change_password(self, _password):
        db.session.query(User).filter(User.id == self.id).update({'password': _password})
        db.session.commit()

    def __repr__(self):
        return "<User {0}> ({1})".format(self.username, self.email)


class NmapTask(db.Model):
    """ NmapTask Class """
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(36))
    comment = db.Column(db.String(128))
    created = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, id=None, comment=None, task_id=None, user=None,
                 created=datetime.datetime.utcnow()):
        self.id = id
        self.comment = comment
        self.task_id = task_id
        self.user_id = user.id
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
        rval = False
        if user is not None and task_id is not None and comment is not None:
            new_nmaptask = NmapTask(user=user,
                                    task_id=task_id, comment=comment)
            db.session.merge(new_nmaptask)
            db.session.commit()
            rval = True
        return rval

    @classmethod
    def remove_task_by_id(cls, task_id=task_id):
        """  """
        result = False

        if task_id is not None:
            nt = NmapTask.query.filter(NmapTask.task_id == task_id).one()
            db.session.delete(nt)
            db.session.commit()
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

""" --- """

class NmapReportMeta(db.Model):
    """ Meta Class for NmapReport

        This class needs to copy data from NmapTask Table that can (and will be
        removed from there.. therefore this can not be implemented as foreigen
        key..

    """

    id = db.Column(db.Integer, primary_key=True)
    # "foreign key"/identifier is the NmapTask.task_id (faef323-afec3-a...)
    task_task_id = db.Column(db.Integer)
    task_comment = db.Column(db.String(128))
    task_created = db.Column(db.DateTime)
    task_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


    def __init__(self, task_id=None):
        self.task_id = task_id
        # TODO .. id ..?! sql.. ? db.session.add(self) + commit()?


    def __repr__(self):
        return "<{0} {1}> TaskID: ({2})".format(
                self.__class__.__name__,
                self.id,
                self.task_id)

    def save_report(self, task_id=None):
        """ TODO """

        _report = NmapTask.get_report(task_id=task_id)

        try:
            dbp = BackendPluginFactory.create(plugin_name="sql",
                                            url=app.config["LIBNMAP_DB_URI"],
                                            echo=False)

            _id = _report.save(dbp)
            r = Address.discover_from_report(report_id=_id)
            print r

            return {"rc": 0}

        except Exception as e:
            print e
            return {"rc": 1}

    @classmethod
    def get_report(cls, report_id):
        """ get one NmapReport """

        dbp = BackendPluginFactory.create(plugin_name='sql',
                                          url=app.config["LIBNMAP_DB_URI"],
                                          echo=False)
        return dbp.get(report_id=report_id)

    @classmethod
    def get_report_by_task_id(cls, report_id=None, task_id=None):
        """ TODO will probably only need either report or task id """
        pass

    @classmethod
    def getall_reports(cls):
        """ getall NmapReport """

        dbp = BackendPluginFactory.create(plugin_name='sql',
                                          url=app.config["LIBNMAP_DB_URI"],
                                          echo=False)
        return dbp.getall()

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
        """ discover hosts from report """

        nmap_report = NmapReportMeta.get_report(report_id)

        if nmap_report:
            for host in nmap_report._hosts:
                print "Address: " +  str(host.address) + " is: " + host.status
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
