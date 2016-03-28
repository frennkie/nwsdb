from django.db import models
# https://docs.djangoproject.com/en/1.8/topics/i18n/timezones/
from django.utils import timezone

from nwscandb.celery import app
from libnmap.parser import NmapParser
from libnmap.objects import NmapReport

from django.contrib.auth.models import User

#from nwscandb.celeryapp import celery_pipe
from celery.states import READY_STATES
from sqlalchemy import asc, desc
import datetime
import json
import uuid

from django.db import transaction
from reversion import revisions as reversion

import logging
logger = logging.getLogger(__name__)

# Create your models here.


class OrgUnit(models.Model):
    """Class for Org

    """

    name = models.CharField(max_length=200)
    comment = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)
    members = models.ManyToManyField(User, through='Membership')

    # one should not override __init__ in django
    @classmethod
    def create(cls, name, email):
        _org_unit = cls(name=name, email=email)
        _org_unit.comment = "foo.. at"
        return _org_unit

    def __repr__(self):
        return "<{0}: {1}>".format(
                self.__class__.__name__,
                self.name)

    def __str__(self):  # __unicode__ on Python 2
        return self.name


class Membership(models.Model):
    """Membership Many-to-Many User to Org (Organization)
    """
    user = models.ForeignKey(User)
    org = models.ForeignKey(OrgUnit)


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

    user = models.ForeignKey(User)
    org_unit = models.ForeignKey(OrgUnit)

    def __repr__(self):
        return "<{0} {1}: {2}>".format(self.__class__.__name__,
                                       self.id,
                                       self.task_id)

    def __str__(self): # __str__ on Python 3
        return self.task_id

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
    report = models.TextField(null=True)

    user = models.ForeignKey(User)
    org_unit = models.ForeignKey(OrgUnit)

    def __repr__(self):
        return "<{0} {1}> TID:{2}".format(self.__class__.__name__,
                                                    self.id,
                                                    self.task_id,
                                                    self.task_comment)
                                                    # self.task_user_id)

    def __str__(self): # __str__ on Python 3
        return self.task_id

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
    def get_nmap_report_by_id(cls, nmap_report_meta_id, user_obj=None):

        if user_obj:
            orgunits = user_obj.orgunit_set.all()
            queryset = NmapReportMeta.objects.filter(org_unit__in=orgunits)
        else:
            queryset = NmapReportMeta.objects.all()

        _nrm = queryset.get(id=nmap_report_meta_id)
        return NmapParser.parse_fromstring(str(_nrm.report))

    @classmethod
    def get_nmap_report_by_task_id(cls, nmap_task_id, user_obj=None):

        if user_obj:
            orgunits = user_obj.orgunit_set.all()
            queryset = NmapReportMeta.objects.filter(org_unit__in=orgunits)
        else:
            queryset = NmapReportMeta.objects.all()

        _nrm = queryset.get(task_id=nmap_task_id)
        return NmapParser.parse_fromstring(str(_nrm.report))

    @classmethod
    def get_nmap_report_as_string_by_task_id(cls, nmap_task_id, user_obj=None):

        if user_obj:
            orgunits = user_obj.orgunit_set.all()
            queryset = NmapReportMeta.objects.filter(org_unit__in=orgunits)
        else:
            queryset = NmapReportMeta.objects.all()

        _report = queryset.get(task_id=nmap_task_id)
        report_as_str = _report.report
        return report_as_str

    @classmethod
    def save_report(cls, task_id=None):
        """This method stores a new NmapReportMeta to db

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
            NmapReportMeta

        Raises:
            MultipleObjectsReturned - if task_id is not unique (should never be the case)
            DoesNotExist - if task_id does not have a corresponding NmapTask in db
            TODO: or is it ObjectDoesNotExist

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
                                     report=_result,
                                     user=User.objects.get(id=_nmap_task.user_id),
                                     org_unit=OrgUnit.objects.get(id=_nmap_task.org_unit_id))
        report_meta.save()

        """
        # call Address.discover which discovers and stores addresses
        r = Address.discover_from_report(report_id=_id)
        """

        return report_meta

    @classmethod
    def save_report_from_import(cls,
                                xml_str=None,
                                comment=None,
                                user=None,
                                org_unit=None):

        """This method stores a new NmapReportMeta to db


        Args:
            xml_str (str):
            comment (str):
            user (User obj):
            org_unit (OrgUnit obj(:

        Returns:
            NmapReportMeta

        """

        fake_task_id = uuid.uuid4()

        try:
            _nmap_report = NmapParser.parse_fromstring(xml_str)

            if isinstance(_nmap_report, NmapReport):
                #print("Debug: NmapReport:")
                #print(_nmap_report)
                pass
            else:
                print("Error: Did not produce a valid NmapReport!")
                raise Exception("Parse Report - Did not produce a valid NmapReport!")

        except Exception as err:
            raise Exception("Parse Report - Something went wrong: {0}".format(err))

        report_meta = NmapReportMeta(task_id=fake_task_id,
                                     task_comment=comment,
                                     task_created=timezone.now(),
                                     report_stored=1,
                                     report=xml_str,
                                     user=user,
                                     org_unit=org_unit)
        report_meta.save()

        return report_meta

    def create_scan_from_report(self):
        pass

    def discover_network_services(self, version_comment=None):
        """ discover all network services from this NmapReportMeta object and store each
        service individually as NetworkService objects

        Args:
            version_comment (str):

        Returns:

        """

        if not self.report_stored:
            raise Exception("No Report stored!")

        _nmap_report = self.get_nmap_report_by_task_id(self.task_id)

        for scanned_host in _nmap_report.hosts:
            for scanned_service in scanned_host.services:
                #
                _proto = scanned_service.protocol.lower()
                # find out how many objects exist with exactly this triple
                nw_list = NetworkService.objects.filter(address=scanned_host.address,
                                                        port=scanned_service.port,
                                                        protocol=_proto)

                if len(nw_list) == 0:
                    # create new NetworkService and initialize revision
                    nw = NetworkService.create(scanned_host.address,
                                               scanned_service.port,
                                               scanned_service.protocol.lower(),
                                               scanned_service.banner,
                                               scanned_service.reason,
                                               scanned_service.service,
                                               scanned_service.state,
                                               self)
                    with transaction.atomic(), reversion.create_revision():
                        reversion.set_user(self.user)
                        if version_comment:
                            reversion.set_comment("initial discovery - {0}".format(version_comment))
                        else:
                            reversion.set_comment("initial discovery")
                        nw.save()

                elif len(nw_list) == 1:
                    # update existing NetworkService and keep revision
                    nw = nw_list[0]

                    nw.banner = scanned_service.banner
                    nw.reason = scanned_service.reason
                    nw.service = scanned_service.service
                    nw.state = scanned_service.state

                    with transaction.atomic(), reversion.create_revision():
                        reversion.set_user(self.user)
                        if version_comment:
                            reversion.set_comment("updated - {0}".format(version_comment))
                        else:
                            reversion.set_comment("updated")
                        nw.save()
                else:
                    print("More that one.. that's wrong")
                    raise Exception("More that one.. that's wrong")

        return True


class NetworkService(models.Model):
    """ A Network Service identified by protocol, address, port (e.g. tcp/127.0.0.1:80)

    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField('date created', auto_now_add=True)
    updated = models.DateTimeField('date update', auto_now=True)

    address = models.CharField(max_length=255)
    port = models.PositiveIntegerField(default=0)

    PROTOCOL_CHOICES = (
        ('tcp', 'TCP'),
        ('udp', 'UDP'),
        ('other', 'Other'),
    )
    protocol = models.CharField(max_length=20, choices=PROTOCOL_CHOICES)

    banner = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    service = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)

    nmap_report_meta = models.ForeignKey(NmapReportMeta)

    # one should not override __init__ in django
    @classmethod
    def create(cls, address, port, protocol, banner, reason, service, state, nmap_report_meta):
        # so then we do the init here
        _network_service = cls(address=address,
                               port=port,
                               protocol=protocol,
                               banner=banner,
                               reason=reason,
                               service=service,
                               state=state,
                               nmap_report_meta=nmap_report_meta)
        return _network_service

    # is a @property done without the @ shortcut + a label for django admin
    def name(self):
        return self.__str__()
    name = property(name)

    def __repr__(self):
        return "<{0}: {1}/{2}:{3}>".format(
                self.__class__.__name__,
                self.protocol,
                self.address,
                self.port)

    def __str__(self):  # __str__ on Python 3
        return "{0}/{1}:{2}".format(
                self.protocol,
                self.address,
                self.port)


class Contact(models.Model):
    """Class for Contact

    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    def __str__(self):  # __str__ on Python 3
        return self.name

