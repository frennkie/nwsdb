from libnmap.parser import NmapParser, NmapParserException
from nmapui.celeryapp import celery_pipe
from bson.objectid import ObjectId
from nmapui import mongo, login_serializer
import hashlib
import datetime

class Users(object):
    @classmethod
    def find(cls, **kwargs):
        _users = []
        _dbusers = mongo.db.users.find(kwargs)
        for _dbuser in _dbusers:
            _users.append(User(id=_dbuser['_id'],
                               username=_dbuser['username'],
                               password=_dbuser['password'],
                               email=_dbuser['email']))
        return _users

    @classmethod
    def get(cls, user_id):
        _user = None
        if isinstance(user_id, unicode):
            user_id = ObjectId(user_id)

        if isinstance(user_id, ObjectId):
            _dbuser = mongo.db.users.find_one({'_id': user_id})
            _user = User(id=_dbuser['_id'],
                         username=_dbuser['username'],
                         password=_dbuser['password'],
                         email=_dbuser['email'])
        return _user

    @classmethod
    def add(cls, username=None, email=None, password=None):
        rval = False
        if username is not None and email is not None and password is not None:
            mongo.db.users.insert({'username': username,
                                   'email': email,
                                   'password': password})
            rval = True
        return rval

class User:
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.password = password
        self.email = email

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
      return False

    def get_id(self):
        return unicode(self.id)

    def get_auth_token(self):
        """
        Encode a secure token for cookie
        """
        data = [str(self.id), self.password]
        return login_serializer.dumps(data)

    def credentials_valid(self, _password):
        return hashlib.sha256(_password).hexdigest() == self.password

    def __repr__(self):
        return "<User {0}>".format(self.username)


class NmapTask(object):
    @classmethod
    def find(cls, asc=True, **kwargs):
        _reports = []

        if asc is True:
            sort_order = 1
        else:
            sort_order = -1

        _dbreports = mongo.db.reports.find(kwargs).sort("created", sort_order)

        for _dbreport in _dbreports:
            _nmap_task = {'task_id': celery_pipe.AsyncResult(_dbreport['task_id']),
                          'comment': _dbreport['comment'],
                          'created': _dbreport['created']}
            _reports.append(_nmap_task)
        return _reports

    @classmethod
    def get(cls, task_id):
        _report = None
        if isinstance(task_id, str) or isinstance(task_id, unicode):
            try:
                _resultdict = celery_pipe.AsyncResult(task_id).result
            except NmapParserException:
                pass
        return _resultdict

    @classmethod
    def get_report(cls, task_id):
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
            mongo.db.reports.insert({'user_id': user_id,
                                     'task_id': task_id,
                                     'comment': comment,
                                     'created': datetime.datetime.utcnow()})
            rval = True
        return rval

    @classmethod
    def remove_task_by_id(cls, task_id=None):
        """
        db.reports.find({'task_id':"727dd22b-edf9-4b2d-a021-0441cedb0c51"})
        db.celery_taskmeta.find({'_id':"727dd22b-edf9-4b2d-a021-0441cedb0c51"})
        """
        result = False
        if task_id is not None:
            mongo.db.reports.remove({'task_id': task_id})
            mongo.db.celery_taskmeta.remove({'_id': task_id})
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

