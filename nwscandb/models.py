import bcrypt
import datetime
from flask.ext.login import UserMixin
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils import IPAddressType
from sqlalchemy import asc, desc

from libnmap.parser import NmapParser, NmapParserException
from libnmap.plugins.backendpluginFactory import BackendPluginFactory
from libnmap.objects.report import NmapReport

from nwscandb import app
from nwscandb import db
from nwscandb import login_serializer
from nwscandb.celeryapp import celery_pipe
from celery.task.control import revoke
from celery.states import READY_STATES, ALL_STATES


class Users(object):
    """Users Class"""

    @classmethod
    def find(cls, **kwargs):
        """find Users from table: users

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
        """get exactly one user identified by ID"""

        _dbuser = User.query.get(user_id)
        _user = User.query.get(_dbuser.id)
        return _user

    @classmethod
    def add(cls, username=None, user_group_name=None, email=None, clear_pw=None, inactive=0):
        """add new user to database"""

        if not (username and user_group_name and email and clear_pw):
            print("Error: username, group, email and clear_pw are all mandatory.")
            raise Exception("Username, group, email and clear_pw are all mandatory.")

        if len(Users.find(username=username)) > 0:
            print("Error: username already in use.")
            raise ValueError("Username already in use.")
        else:
            user_group = UserGroup.get_or_create_by_name(name=user_group_name)
            if user_group is None:
                raise Exception("Problem with UserGroup: " + user_group_name)
            else:
                new_user = User(username=username,
                                email=email,
                                clear_pw=clear_pw,
                                inactive=inactive)
                user_group.users.append(new_user)
                db.session.add(new_user)
                db.session.commit()
                return new_user


class User(db.Model, UserMixin):
    """User Class and SQL Table"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password = db.Column(db.String(128))
    email = db.Column(db.String(128))
    inactive = db.Column(db.SmallInteger)
    created = db.Column(db.DateTime)
    last_login = db.Column(db.DateTime)
    last_update = db.Column(db.DateTime, default=datetime.datetime.utcnow(),
                            onupdate=datetime.datetime.utcnow(), nullable=False)
    sso_enabled = db.Column(db.SmallInteger)

    nmaptasks = db.relationship('NmapTask', backref=db.backref('nmaptask'))

    user_group_id = db.Column(db.Integer, db.ForeignKey('user_group.id'))

    def __init__(self, id=None,
                 username=None,
                 user_group_id=None,
                 email=None,
                 clear_pw=None,
                 inactive=0,
                 sso_enabled=0):
        # TODO id should not be set.. but username, clear_pw (and maybe email) are mandatory!

        if username is None:
            raise Exception("Username can not be empty")

        self.id = id
        self.username = username
        self.user_group_id = user_group_id
        _pw = bcrypt.hashpw(clear_pw + app.config["PEPPER"], bcrypt.gensalt())
        self.password = _pw
        self.email = email
        self.inactive = inactive
        self.sso_enabled = sso_enabled
        self.created = datetime.datetime.utcnow()

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

    def update_last_login(self):
        self.last_login = datetime.datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def has_permission(self, name=None):
        return True


class UserGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    comment = db.Column(db.String(128))

    users = db.relationship('User', backref=db.backref('user_group'))

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
        """Add new UserGroup"""
        if name is None:
            print("name is required!")
            raise Exception("name is required!")
        if id and name != "admin":
            print("Error: don't hardcode Permission IDs (except for admin).")
            raise Exception("Don't hardcode Permission IDs (except for admin).")

        _new_user_group = UserGroup(id=id, name=name, comment=comment)
        db.session.add(_new_user_group)
        db.session.commit()
        return _new_user_group

    @classmethod
    def get_or_create_by_name(cls, name=None):
        """get or create a user group by name


        Args:
            cls: class itself
            name (str): name of group that may of may not exist

        Returns:
            Object of Class UserGroup or None

        """

        try:
            res = UserGroup.query.filter_by(name=name).one()
            return res
        except NoResultFound:
            return UserGroup.add(name=name, comment="_auto_created_")
        except Exception as err:
            print("Failed to get_or_create Group: " + str(err))
            return None


class NmapTask(db.Model):
    """ NmapTask Class """
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(36))
    comment = db.Column(db.String(128))
    created = db.Column(db.DateTime)
    completed = db.Column(db.SmallInteger)
    completed_status = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __init__(self, id=None, comment=None, task_id=None, user=None,
                 created=None, completed=0):
        self.id = id
        self.comment = comment
        self.task_id = task_id
        self.user_id = user.id
        self.created = created
        self.completed = completed
        self.async_result = None

    def __repr__(self):
        return "<{0} {1}: {2}>".format(self.__class__.__name__,
                                       self.id,
                                       self.task_id)

    def append_async_result(self):
        """Will get the async_result information (if still there)

        The AsyncResult object is the celery object that exists until the Task
        is removed from the celery backend (usually after a few days).
        As long as the AsyncResult inforamtion is still there this method will
        retrieve it and add it as an attribute to the current NmapTask.
        This can be called as soon as a Task was created, while the task is
        running and for a short time after the Task is finished.

        Args:
            None

        Returns:
            True if "async_result" attr was set, False if not

        """

        async_result_obj = celery_pipe.AsyncResult(self.task_id)

        self.async_result = async_result_obj

        if async_result_obj.status == "PENDING":
            if self.completed == 1:
                self.completed_status = "REMOVED"
            else:
                self.completed_status = "PENDING"

        else:
            self.completed_status = async_result_obj.status

        return True

    @classmethod
    def find(cls, sort_asc=True, **kwargs):
        _nmap_tasks = []

        if sort_asc is True:
            _db_nmap_tasks = NmapTask.query.filter_by(**kwargs).order_by(asc("id")).all()
        else:
            _db_nmap_tasks = NmapTask.query.filter_by(**kwargs).order_by(desc("id")).all()

        for _db_nmap_task in _db_nmap_tasks:
            _db_nmap_task.append_async_result()
            _nmap_tasks.append(_db_nmap_task)

        return _nmap_tasks

    @classmethod
    def get_by_task_id(cls, task_id=None):
        """This classmethod gets a NmapTask object by it's task_id.

        Args:
            cls (cls): The class itself (not an instance)
            task_id (str): The task_id as a string (e.g faef323-afec3-a...)

        :rtype : NmapTask
        Returns:
            Either exactly one NmapTask object or None

        Raises:
            Exception: If more than one result is found.

        Examples:
            >>> NmapTask.get_by_task_id(task_id="foo_bar") is None
            True

            >>> isinstance(NmapTask.get_by_task_id(
                           task_id="98d8872b-c0ce-4bdc-ba72-d9cf98f8383e"), NmapTask)
            True

        """

        _db_nmap_task_list = NmapTask.query.filter_by(task_id=task_id).all()
        _length = len(_db_nmap_task_list)

        if _length == 0:
            return None
        elif _length == 1:
            return _db_nmap_task_list[0]
        else:
            print("Error: Found more that 1 result for Task ID: " + task_id)
            raise Exception("Error: Found more that 1 result for Task ID: " + task_id)

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

    def delete(self):
        """delete this NmapTask"""

        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            print("Error: " + str(e))
            return False

    @classmethod
    def stop_task_by_id(cls, task_id=task_id):
        """  """
        print("This is not implemented!")
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
            old_report = NmapParser.parse_fromfile('nwscandb/test/1_hosts.xml')
            new_report = NmapParser.parse_fromfile('nwscandb/test/1_hosts_diff.xml')

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


class SubNmapReport(NmapReport):
    """Sub Class to Report Class"""

    @classmethod
    def get_report_from_async_result(cls, task_id):
        """This classmethod gets a NmapReport object by the task_id.

        The NmapReport is constructed on demand from the AsyncResult object. This can
        only produce a valid result if the Celery Task is finished already.

        Args:
            cls (cls): The class itself (not an instance)
            task_id (str): task_id

        Note:
            This currently is a Sub-Class of NmapReport. Maybe this can be done more
            transparently (what's with super?). TODO

        Returns:
            NmapReport object

        """

        try:
            _resultdict = celery_pipe.AsyncResult(task_id).result
            _resultxml = _resultdict['report']
            _report = NmapParser.parse_fromstring(_resultxml)
            return _report
        except NmapParserException as e:
            print e
            return None


    @classmethod
    def get_all_reports(cls):
        """This classmethod gets a list of all NmapReport.

        This is done using the libnmap SQL Plugin.

        Args:
            cls (cls): The class itself (not an instance)

        Returns:
            List of NmapReport object

        """

        dbp = BackendPluginFactory.create(plugin_name='sql',
                                          url=app.config["LIBNMAP_DB_URI"],
                                          echo=False)
        return dbp.getall()


    @classmethod
    def get_report(cls, report_id):
        """This classmethod gets one NmapReport by report_id.

        This is done using the libnmap SQL Plugin.

        Args:
            cls (cls): The class itself (not an instance)
            report_id (int): report_id

        Returns:
            NmapReport object

        """

        dbp = BackendPluginFactory.create(plugin_name='sql',
                                          url=app.config["LIBNMAP_DB_URI"],
                                          echo=False)
        return dbp.get(report_id=report_id)


class NmapReportMeta(db.Model):
    """ Meta Class for NmapReport

        This class needs to copy data from NmapTask Table that can (and will be
        removed from there.. therefore this can not be implemented as foreign
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

    def __init__(self):
        pass
        # TODO .. id ..?! sql.. ? db.session.add(self) + commit()?

    def __repr__(self):
        return "<{0} {1}> TID:{2}, User:{4}".format(self.__class__.__name__,
                                                    self.id,
                                                    self.task_task_id,
                                                    self.task_comment,
                                                    self.task_user_id)

    @classmethod
    def get_report_meta(cls, **kwargs):
        """This classmethod gets a list of all NmapReportMeta objects.

        List can be filtered by using the keyword arguments. E.g. only db row for a
        certain user_id can be requested.

        Args:
            **kwargs

        Returns:
            List of NmapReportMeta objects
        """

        return NmapReportMeta.query.filter_by(**kwargs).order_by(asc("id")).all()


    @classmethod
    def get_report_id_by_task_id(cls, task_id=None):
        """This classmethod get the report_id integer value for a task_id.

        Args:
            task_id (str): The task_id as a string (e.g faef323-afec3-a...)

        Returns:
            report_id (int) or None

        Raises:
            Exception if more that one result is found for task_id

        Examples:

        """

        _db_nmap_report_meta_list = NmapReportMeta.query.filter_by(task_task_id=task_id).all()
        _length = len(_db_nmap_report_meta_list)

        if _length == 0:
            return None
        elif _length == 1:
            return _db_nmap_report_meta_list[0].report_id
        else:
            print("Error: Found more that 1 result for Task ID: " + task_id)
            raise Exception("Error: Found more that 1 result for Task ID: " + task_id)

    def save_report(self, task_id=None):
        """This method stores the NmapReportMeta and NmapReport to db

        Call this method right after the Celery Task is finished.
        It will
        * get a NmapTask object (by the task_id) from db
        * get a NmapReport object (created from AsyncResult)
        * update the NmapTask completed (+ c_status) field in the db to 1
        * save that NmapReport to db table "reports"
        * save the newly create NmapReportMeta object to db

        Args:
            task_id (str): The task_id as a string (e.g faef323-afec3-a...)

        Returns:
            True or False

        Raises:

        Examples:

        """

        try:
            _nmap_task = NmapTask.get_by_task_id(task_id=task_id)
        except:
            return False

        if _nmap_task is None:
            return False


        # mark nmap_task as done in table
        _nmap_task.completed = 1
        _nmap_task.append_async_result()
        db.session.commit()

        _report = SubNmapReport.get_report_from_async_result(task_id=task_id)

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

            return True

        except Exception as e:
            print e
            return False

    def create_scan_from_report(self):
        pass


contact_addressdetail_table = db.Table("contact_addressdetail",
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
    contact = db.relationship("Contact", secondary=contact_addressdetail_table)

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
        return "<{0} {1}> ({5}) N:({3}) IP: {6}".format(self.__class__.__name__,
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
    address_detail = db.relationship("AddressDetail", secondary=contact_addressdetail_table)

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

    def __init__(self, address=None):
        self.address = address

    def __repr__(self):
        return "<{0} {1}>".format(self.__class__.__name__,
                                  self.address)

    @classmethod
    def discover_from_report(cls, report_id):
        """discover hosts from report and store in db"""

        nmap_report = SubNmapReport.get_report(report_id)

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

        nmap_report_list = SubNmapReport.get_all_reports()

        all_addresses = []
        for report_id, report_obj in nmap_report_list:
            # print str(report_id) + ": " + str(report_obj)
            # print report_obj._hosts
            for host in report_obj._hosts:
                all_addresses.append({"address": host.address,
                                      "report_id": report_id})

        print "\n---\n"
        print all_addresses

