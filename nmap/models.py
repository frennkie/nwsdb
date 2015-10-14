from django.db import models
# https://docs.djangoproject.com/en/1.8/topics/i18n/timezones/
from django.utils import timezone

from nwscandb.celery import app
from libnmap.parser import NmapParser
from libnmap.objects import NmapReport

#from nwscandb.celeryapp import celery_pipe
from celery.states import READY_STATES
from sqlalchemy import asc, desc
import datetime
import json

# Create your models here.


class NmapTask(models.Model):
    """ NmapTask Class

    """
    class Meta:
        permissions = (
            ("view_task", "Can see tasks"),
            ("stop_task", "Can stop running tasks"),
            ("revoke_task", "Can revoke pending tasks"),
        )

    task_id = models.CharField(max_length=36)
    comment = models.CharField(max_length=200)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)
    completed = models.BooleanField(default=False)
    completed_status = models.CharField(max_length=20)

    #user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return "<{0} {1}: {2}>".format(self.__class__.__name__,
                                       self.id,
                                       self.task_id)

    @classmethod
    def find(cls, sort_desc=False, **kwargs):
        """Get NmapTask object and add async_result before returning

        Result can be filtered by kwargs (e.g. only for specific User or Group

        Returns:
            List of NmapTask objects (empty list if none found)

        """

        if sort_desc is False:
            return NmapTask.objects.filter(**kwargs).order_by('created')
        else:
            return NmapTask.objects.filter(**kwargs).order_by('-created')

    @classmethod
    def get_by_task_id(cls, task_id=None):
        """This classmethod gets a NmapTask object by it's task_id.

        Args:
            cls (cls): The class itself (not an instance)
            task_id (str): The task_id as a string (e.g faef323-afec3-a...)

        Returns:
            Either exactly one NmapTask object or None

        Raises:
            Exception: If more than one result is found.

        Examples:
            >>> NmapTask.get_by_task_id(task_id="foo_bar") is None
            True

            >>> isinstance(NmapTask.get_by_task_id(task_id="98d8872b-c0ce-4bdc-ba72-d9cf98f8383e"), NmapTask)
            True

        """

        _db_nmap_task_list = NmapTask.objects.filter(task_id=task_id)
        _length = len(_db_nmap_task_list)

        if _length == 0:
            return None
        elif _length == 1:
            return _db_nmap_task_list[0]
        else:
            print("Error: Found more that 1 result for Task ID: " + task_id)
            raise Exception("Error: Found more that 1 result for Task ID: " + task_id)

    def get_task_result(self):
        from nmap.tasks import get_scan_task_result
        return get_scan_task_result(self.task_id)

    @classmethod
    def get_tasks_status_as_dict(cls, **kwargs):
        """Get the status of one task and return JSON (dict) result"""

        _nmap_tasks = NmapTask.objects.filter(**kwargs).order_by('created')

        _jtarray = []
        for _nmap_task in _nmap_tasks:
            _status_dict = {'id': str(_nmap_task.task_id),
                            'status': _nmap_task.completed_status,
                            'progress': 0,
                            'ready': 0}
            if _nmap_task.completed == 1:
                _status_dict.update({'status': str(_nmap_task.completed_status)})
                _status_dict.update({'progress': 100})
                _status_dict.update({'ready': 1})
                _status_dict.update({'etc': 0})

                _jtarray.append(_status_dict)
            else:
                # tasks not marked as completed. Let's check celery task for status
                from nmap.tasks import get_scan_task_status
                _status_dict = get_scan_task_status(_nmap_task.task_id)

                _jtarray.append(_status_dict)

        return _jtarray


    @classmethod
    def stop_task_by_id(cls, task_id=task_id):
        """Cancel the execution of a task that is not yet running"""

        print("trying to stop " + task_id)

        from nmap.tasks import get_scan_task_status

        _scan_task_status = get_scan_task_status(task_id)
        if _scan_task_status['status'] == "PENDING":
            app.control.revoke(task_id)
            return True
        else:

            app.control.revoke(task_id, terminate=True, signal="SIGKILL")
            return False

        """
            #revoke(task_id, terminate=True, signal="SIGUSR1")  SIGKILL
            revoke(task_id, terminate=True)
        """

    @classmethod
    def cancel_pending_task_by_id(cls, task_id=task_id):
        """Cancel the execution of a task that is not yet running"""

        from nmap.tasks import get_scan_task_status

        print("trying to stop " + task_id)

        _scan_task_status = get_scan_task_status(task_id)
        if _scan_task_status['status'] == "PENDING":
            app.control.revoke(task_id)
            return True
        else:
            print("not PENDING!")
            return False


class NmapReportMeta(models.Model):
    """ Meta Class for NmapReport

        This class needs to copy data from NmapTask Table that can (and will be
        removed from there.. therefore this can not be implemented as foreign
        key..

    """

    task_id = models.CharField(max_length=36)
    task_comment = models.CharField(max_length=200)
    task_created = models.DateTimeField('date task created', null=True)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)

    report_stored = models.BooleanField(default=False)
    #report_id = models.IntegerField(null=True)
    report = models.TextField(null=True)
    #task_user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return "<{0} {1}> TID:{2}".format(self.__class__.__name__,
                                                    self.id,
                                                    self.task_id,
                                                    self.task_comment)
                                                    # self.task_user_id)

    @classmethod
    def get_report_meta(cls, **kwargs):
        """This classmethod gets a list of all NmapReportMeta objects.

        List can be filtered by using the keyword arguments. E.g. only db row for a
        certain user_id can be requested.
        If you need to get only exactly one the use Obj.objects.get(Field=Value)

        Args:
            **kwargs

        Returns:
            List of NmapReportMeta objects
        """

        #return NmapReportMeta.query.filter_by(**kwargs).order_by(asc("id")).all()
        return NmapReportMeta.objects.filter(**kwargs).order_by('created')

    @classmethod
    def get_nmap_report_by_id(cls, nmap_report_meta_id):
        _nrm = NmapReportMeta.objects.get(task_id=nmap_report_meta_id)
        return NmapParser.parse_fromstring(str(_nrm.report))

    @classmethod
    def get_nmap_report_by_task_id(cls, nmap_task_id):
        _nrm = NmapReportMeta.objects.get(task_id=nmap_task_id)
        return NmapParser.parse_fromstring(str(_nrm.report))

    @classmethod
    def save_report(cls, task_id=None):
        """This method stores a new NmapReportMeta and NmapReport to db

        Call this method right after the Celery Task is finished.
        It will
        * get a NmapTask object (by the task_id) from db
        * get the task result and create NmapReport object from result string
        * save that NmapReport to
        * update the NmapTask completed (+ c_status) field in the db to 1
        * save the newly create NmapReportMeta object to db

        Args:
            task_id (str): The task_id as a string (e.g faef323-afec3-a...)

        Returns:
            True or False

        Raises:
            MultipleObjectsReturned - if task_id is not unique (should never be the case)
            DoesNotExist - if task_id does not have a corresponding NmapTask in db

        Examples:

        """

        _nmap_task = NmapTask.objects.get(task_id=task_id)
        _status = NmapTask.get_tasks_status_as_dict(task_id=task_id)[0]['status']
        _result = str(_nmap_task.get_task_result())
        try:
            _nmap_report = NmapParser.parse_fromstring(_result)

            if isinstance(_nmap_report, NmapReport):
                print("Debug: NmapReport:")
                print(_nmap_report)
            else:
                print("Error: Did not produce a valid NmapReport!")

        except Exception as err:
            print("Parse Report - Something went wrong: " + str(err))

        _nmap_task.completed = 1
        _nmap_task.completed_status = _status
        _nmap_task.save()

        report_meta = NmapReportMeta(task_id=_nmap_task.task_id,
                                     task_comment=_nmap_task.comment,
                                     task_created=_nmap_task.created,
                                     report_stored=1,
                                     report=_result)
        report_meta.save()

        """
        # call Address.discover which discovers and stores addresses
        r = Address.discover_from_report(report_id=_id)
        """

        return True


    def create_scan_from_report(self):
        pass


class Contact(models.Model):
    """Class for Contact

    """

    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200, blank=True)
    comment = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)
    #address_detail = db.relationship("AddressDetail", secondary=contact_addressdetail_table)

    # one should not override __init__ in django
    @classmethod
    def create(cls, name, email):
        _contact = cls(name=name, email=email)
        _contact.comment = "foo.. at: " + str(timezone.now()) + "!"
        return _contact

    def __repr__(self):
        return "<{0} {1}> Name: ({3}) Mail: ({4})".format(
                self.__class__.__name__,
                self.id,
                self.created,
                self.name,
                self.email)

    def __unicode__(self): # __str__ on Python 3
        return self.name

