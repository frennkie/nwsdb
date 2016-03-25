from django.views.generic import TemplateView, View
from django.views.generic.base import ContextMixin
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.db.models import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.core.urlresolvers import resolve
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.contrib.auth import logout

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.mixins import LoginRequiredMixin

from djqscsv import render_to_csv_response
from xlsx import Workbook

import json
import logging
import datetime
import re

# start import from my models
from nmap.tasks import celery_nmap_scan
from .models import Contact, NmapTask, NmapReportMeta, OrgUnit, NetworkService
from django.contrib.auth.models import User
from django import forms
from .forms import ScanForm

logger = logging.getLogger(__name__)

"""
def get_remote_user(_request):
    # Return remote_user (value is None if empty)

    try:
        remote_user = _request.META['REMOTE_USER']
    except KeyError:
        remote_user = None
    return remote_user
"""

"""
This is the standard layout for a authenticated view to a html template.
call with:
url(r'^some/$', SomeView.as_view(), name='some_view'),
or
url(r'^some/(?P<some_id>[0-9]+)$',  SomeView.as_view(), name='some_view'),

class SomeView(PermissionRequiredMixin, TemplateView):
    permission_required = "nmap.permission_name"
or
class SomeView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        # get - context provides some_id
        context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        or
        context = {}
        template_name = 'nmap/template_file.html'


        some = SomeClass.objects.all()
        other_stuff = OtherStuff.objects.all()

        context = {}
        context.update({"some": some,
                       "other_stuff": other_stuff})
        return render(request, template_name, context)

"""


class Index(TemplateView):
    """Index"""

    def get(self, request, *args, **kwargs):
        # get - context provides nothing
        # context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        context = {}

        template_name = "nmap/index.html"

        """ DEBUG INFO """

        view_name = request.resolver_match.url_name
        logger.debug(view_name)

        logger.debug("user: " + str(request.user))
        #logger.debug("remote_user: " + str(remote_user))
        logger.debug("Authenticated: " +  str(request.user.is_authenticated()))
        logger.debug("Superuser: "  + str(request.user.is_superuser))
        logger.debug("Groups: "  + str(request.user.groups.count()))

        logger.debug("foo bar")

        """ /DEBUG INFO """

        if request.user.is_authenticated():
            if request.user.is_superuser:
                logger.debug("you can do and see anything")
                # _contacts = Contact.objects.all()
            else:

                if request.user.groups.count() == 0:
                    logger.debug("no groups assigned")
                elif request.user.groups.count() == 1:
                    logger.debug("exactly one group.. that's normal (=nice)")
                else:
                    logger.debug("hm.. why do you have more than one group?!")
        else:
            logger.debug("non-auth")

        """ TODO remove this block.. """
        if request.user.is_authenticated():
            messages.success(request, "Welcome " + str(request.user))
        else:
            messages.error(request, "You do not have permission to access this site!")
        """ TODO remove this block.. """

        _contacts = Contact.objects.all()

        context.update({"contacts": _contacts,
                        "view_name": view_name})
        return render(request, template_name, context)



""" NWScanDB Models Start here """


class ScanView(PermissionRequiredMixin, TemplateView):
    """Scan View"""

    permission_required = "nmap.view_scan"

    def get(self, request, *args, **kwargs):
        # get - context provides nothing
        # context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        context = {}
        template_name = "nmap/scan.html"

        # u = User.objects.get(username=get_remote_user(request))
        u = User.objects.get(username=request.user)
        org_units = u.orgunit_set.all()

        if len(org_units):
            form = ScanForm(initial={'org_unit': org_units[0].id})
        else:
            form = ScanForm(initial={})

        form.fields['org_unit'].queryset = u.orgunit_set

        context.update({"form": form,
                        "org_units": org_units})
        return render(request, template_name, context)


class TasksJsonView(PermissionRequiredMixin, TemplateView):
    """Task Json View

    Get a list of all tasks that the User is is allowed to see.
    Filter either for user id or for group (membership)
    Return result as JSON dump so that the progress bar can be drawn with AJAX

    """

    permission_required = "nmap.view_task"

    def get(self, request, *args, **kwargs):
        """TODO: get current user/group for filter"""

        # u = User.objects.get(username=get_remote_user(request))
        u = User.objects.get(username=request.user)
        orgunits = u.orgunit_set.all()

        _result = NmapTask.get_tasks_status_as_dict(org_unit__in=orgunits)
        return HttpResponse(json.dumps(_result), content_type="application/json")


class TasksView(PermissionRequiredMixin, TemplateView):
    """Tasks View

    get and post

    """

    permission_required = "nmap.view_task"

    def get(self, request, *args, **kwargs):
        # get - context provides nothing
        # context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        context = {}
        template_name = "nmap/tasks.html"

        # u = User.objects.get(username=get_remote_user(request))
        u = User.objects.get(username=request.user)
        orgunits = u.orgunit_set.all()
        _nmap_task = NmapTask.objects.filter(org_unit__in=orgunits)

        #context.update({"remote_user": get_remote_user(request)})
        context.update({"orgunits": orgunits})
        context.update({"nmap_tasks": _nmap_task})
        return render(request, template_name, context)

    def post(self, request, *args, **kwargs):
        """post"""

        # u = User.objects.get(username=get_remote_user(request))
        u = User.objects.get(username=request.user)
        org_units = u.orgunit_set.all()

        form = ScanForm(request.POST)
        if not form.is_valid():
            template_name = "nmap/scan.html"
            form.fields['org_unit'].queryset = u.orgunit_set

            context = {}
            context.update({"form": form})
            context.update({"org_units": org_units})
            return render(request, template_name, context)

        logger.debug("Form is valid!")

        targets = form.cleaned_data["targets"]
        comment = form.cleaned_data['comment']

        no_ping = request.POST.get('no_ping', False)
        banner_detection = request.POST.get('banner_detection', False)
        os_detection = request.POST.get('os_detection', False)
        run_now = request.POST.get('run_now', False)

        if no_ping:
            logger.debug("no_ping was selected. ")
        if banner_detection:
            logger.debug("banner_detection was selected.")
        if os_detection:
            logger.debug("os_detection was selected.")
        if run_now or not run_now:
            logger.debug("run_now is currently disabled.")

        # as this has been validated.. it must be an OrgUnit obj
        org_unit = form.cleaned_data['org_unit']

        # isn't this validation?!
        scan_types = [ "-sT", "-sT", "-sS", "-sA", "-sW", "-sM",
                "-sN", "-sF", "-sX", "-sU" ]

        _scan_type = scan_types[int(form.cleaned_data['scan_type'])]

        if form.cleaned_data["ports"]:
            _portlist = "-p " + form.cleaned_data["ports"]
        else:
            _portlist = ""

        logger.debug("ports list")
        logger.debug(_portlist)

        if form.cleaned_data["top_ports"]:
            _top_portlist = "--top-ports " + str(form.cleaned_data["top_ports"])
        else:
            _top_portlist = ""

        logger.debug("top ports")
        logger.debug(_top_portlist)

        _no_ping = "-P0" if no_ping else ""
        _os_detection = "-O" if os_detection else ""
        _banner_detection = "-sV" if banner_detection else ""

        _options = "{0} {1} {2} {3} {4} {5}".format(_scan_type,
                                                _top_portlist,
                                                _portlist,
                                                _no_ping,
                                                _os_detection,
                                                _banner_detection)
        # remove double blanks
        options = re.sub(" +"," ", _options)


        """ use either eta OR countdown! """

        """
        _c_eta = datetime.datetime.utcnow() + datetime.timedelta(seconds=0)
        _c_exp = datetime.datetime.utcnow() + CELERY_TASK_EXPIRES
        _celery_task = celery_nmap_scan.apply_async(eta=_c_eta,
                                                    expires=_c_exp,
                                                    kwargs={'targets': str(targets),
                                                            'options': str(options)})
        """
        _ctask = celery_nmap_scan.apply_async(kwargs={'targets': str(targets),
                                                      'options': str(options)})

        nt = NmapTask(task_id=_ctask.id,
                      comment=comment,
                      user=u,
                      org_unit=org_unit)
        nt.save()

        return redirect('nmap:tasks')


class TaskDelete(PermissionRequiredMixin, TemplateView):
    """Tasks Delete"""

    permission_required = "nmap.delete_nmaptask"

    def get(self, request, *args, **kwargs):
        # get - context provides 'task_id'
        context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)

        try:
            _nmap_task = NmapTask.objects.get(task_id=context['task_id'])
            _nmap_task.delete()
        except ObjectDoesNotExist:
            messages.error(request, "does not exist!")
            # TODO 2016-03-25 (RH): why accounts login?!
            return render(request, 'accounts/login.html')

        return redirect("nmap:tasks")


class NmapReportsView(PermissionRequiredMixin, TemplateView):
    """NmapReports View takes task_id"""

    permission_required = "nmap.view_task"

    def get(self, request, *args, **kwargs):
        # get - context provides nothing
        # context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        context = {}
        template_name = "nmap/reports.html"

        """
        _nmap_report = NmapReportMeta.get_nmap_report_by_task_id(task_id)
        for scanned_host in _nmap_report.hosts:

            scanned_host.datetime_starttime = datetime.datetime.fromtimestamp(int(scanned_host.starttime))
            scanned_host.datetime_endtime = datetime.datetime.fromtimestamp(int(scanned_host.endtime))

            scanned_host.get_open_ports_count = len(scanned_host.get_open_ports())
        """

        # u = User.objects.get(username=get_remote_user(request))
        u = User.objects.get(username=request.user)
        orgunits = u.orgunit_set.all()
        nmap_reports = NmapReportMeta.objects.filter(org_unit__in=orgunits)

        paginator = Paginator(nmap_reports, 15)

        page = request.GET.get('page')

        try:
            items_paged = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items_paged = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items_paged = paginator.page(paginator.num_pages)

        #context.update({"remote_user": get_remote_user(request)})
        context.update({"items_paged": items_paged})

        return render(request, template_name, context)


class NmapReportView(PermissionRequiredMixin, TemplateView):
    """NmapReport View takes task_id"""

    permission_required = "nmap.view_task"

    def get(self, request, *args, **kwargs):
        # get - context provides "task_id"
        context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        template_name = 'nmap/report.html'

        # u = User.objects.get(username=get_remote_user(request))
        u = User.objects.get(username=request.user)

        _nmap_report = NmapReportMeta.get_nmap_report_by_task_id(context['task_id'], user_obj=u)
        for scanned_host in _nmap_report.hosts:

            scanned_host.datetime_starttime = datetime.datetime.fromtimestamp(int(scanned_host.starttime))
            scanned_host.datetime_endtime = datetime.datetime.fromtimestamp(int(scanned_host.endtime))

            scanned_host.get_open_ports_count = len(scanned_host.get_open_ports())

        context.update({"report": _nmap_report})
        return render(request, template_name, context)


class NmapReportXMLView(PermissionRequiredMixin, TemplateView):
    """NmapReport XML View takes task_id"""
    permission_required = "nmap.view_task"

    def get(self, request, *args, **kwargs):
        # get - context provides "task_id"
        context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        # u = User.objects.get(username=get_remote_user(request))
        u = User.objects.get(username=request.user)
        n = NmapReportMeta.get_nmap_report_as_string_by_task_id(context['task_id'], user_obj=u)
        return HttpResponse(n, content_type="text/plain; charset=utf-8")


class NmapReportXMLGet(PermissionRequiredMixin, View):
    """NmapReport XML Get takes task_id"""
    permission_required = "nmap.view_task"

    def get(self, request, *args, **kwargs):
        # get - context provides "task_id"
        context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        # u = User.objects.get(username=get_remote_user(request))
        u = User.objects.get(username=request.user)
        n = NmapReportMeta.get_nmap_report_as_string_by_task_id(context['task_id'], user_obj=u)
        return HttpResponse(n, content_type="application/force-download; charset=utf-8")


class NmapReportIDView(PermissionRequiredMixin, TemplateView):
    """NmapReportID View - same as NmapReportView but takes id instead of task_id """

    permission_required = "nmap.view_task"

    def get(self, request, *args, **kwargs):
        # get - context provides "report_id"
        context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        template_name = 'nmap/report.html'

        logger.debug("foo bar")
        logger.debug(context)
        logger.debug(type(context))
        _nmap_report = NmapReportMeta.get_nmap_report_by_id(context['report_id'])

        context.update({"report": _nmap_report})
        logger.debug(context)
        return render(request, template_name, context)


class NetworkServicesView(PermissionRequiredMixin, TemplateView):
    """NetworkServices View takes task_id"""

    permission_required = "nmap.view_task"

    def get(self, request, *args, **kwargs):
        # get - context provides nothing
        # context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        context = {}
        template_name = "nmap/services.html"


        # u = User.objects.get(username=get_remote_user(request))
        u = User.objects.get(username=request.user)

        network_services = NetworkService.objects.all()

        paginator = Paginator(network_services, 40)

        page = request.GET.get('page')

        try:
            items_paged = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items_paged = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items_paged = paginator.page(paginator.num_pages)

        #context.update({"remote_user": get_remote_user(request)})
        context.update({"items_paged": items_paged})

        return render(request, template_name, context)


class NetworkServicesGet(PermissionRequiredMixin, View):
    """Network Services get all """
    permission_required = "nmap.view_task"

    def get(self, request, *args, **kwargs):
        # get and return as CSV (only selected fields)
        # nw = NetworkService.objects.all()
        nw = NetworkService.objects.all().values('updated',
                                                 'protocol',
                                                 'address',
                                                 'port',
                                                 'service',
                                                 'state',
                                                 'reason',
                                                 'banner',
                                                 'nmap_report_meta_id')
        return render_to_csv_response(nw)


class NmapXMLImport(PermissionRequiredMixin, TemplateView):
    """NMAP XML Import View"""
    permission_required = "nmap.view_task"

    def get(self, request, *args, **kwargs):
        # get - context provides nothing
        # context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        context = {}
        template_name = "nmap/import_nmap_xml.html"

        return render(request, template_name, context)

    def post(self, request, *args, **kwargs):
        # post - get file from request
        import_file = request.FILES['file']
        if import_file:
            # get user an first Org (TODO: make Org chosable)
            u = User.objects.get(username=request.user)
            org_units = u.orgunit_set.all()
            o = org_units[0]
            # get content of uploaded file
            content = import_file.read()

            try:
                nmr = NmapReportMeta.save_report_from_import(content, "Manual Imported", u, o)
            except Exception as err:
                logger.error("nmap_import failed: {0}".format(err))
                logger.debug("nmap_import failed: {0}".format(err))
                return JsonResponse({"result": "failed",
                                     "message": "could not parse file"})

            try:
                nmr.discover_network_services()
            except Exception as err:
                logger.error("discover NetworkService objects failed: {0}".format(err))
                logger.debug("discover NetworkService objects failed: {0}".format(err))

            return JsonResponse({"result": "success",
                                 "message": "all clear",
                                 "NmapResultMeta": "{0}".format(nmr.__repr__())})
        else:
            return JsonResponse({"result": "failed",
                                 "message": "no file provided?!"})


class ImportView(PermissionRequiredMixin, TemplateView):
    """Import View"""
    permission_required = "nmap.view_task"

    def get(self, request, *args, **kwargs):
        # get - context provides nothing
        # context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        context = {}
        template_name = "nmap/import.html"

        #context.update({"import": "import"})
        return render(request, template_name, context)

    def post(self, request, *args, **kwargs):
        # post -
        context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        template_name = "nmap/import_result.html"

        import_file = request.FILES['file']
        if import_file:
            book = Workbook(import_file) #Open xlsx file
            sheets = []
            for sheet in book:
                    print sheet.name
                    sheets.append(sheet)
            content = import_file.read()

            context.update({"sheets": sheets})
            return render(request, template_name, context)
        else:
            raise Exception("nmap_import failed")




"""sample:

"""
