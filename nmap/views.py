from django.views.generic import TemplateView
from braces.views import MessageMixin, LoginRequiredMixin, GroupRequiredMixin
from braces.views import PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.db.models import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.core.urlresolvers import resolve
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.contrib.auth import logout

from xlsx import Workbook

import json
import datetime
import re

# start import from my models
from nmap.tasks import celery_nmap_scan
from .models import Contact, NmapTask, NmapReportMeta, OrgUnit
from django.contrib.auth.models import User
from django import forms
from .forms import ScanForm


def get_remote_user(_request):
    """Return remote_user (value is None if empty)"""

    try:
        remote_user = _request.META['REMOTE_USER']
    except KeyError:
        remote_user = None
    return remote_user


"""
This is the standard layout for a authenticated view to a html template.
call with: url(r'^some/$', SomeView.as_view(), name='some_view'), :

class SomeView(LoginRequiredMixin, TemplateView):
    def get(self, request):

        some = SomeClass.objects.all()
        other_stuff = OtherStuff.objects.all()

        cdict = {}
        cdict.update({"some": some,
                       "other_stuff": other_stuff})
        return render(request, 'nmap/index.html', cdict)

"""


def index(request):
    """index"""


    """ DEBUG INFO """

    remote_user = get_remote_user(request)

    view_name = request.resolver_match.url_name
    print(view_name)

    print("user: " + str(request.user))
    print("remote_user: " + str(remote_user))
    print("Authenticated: " +  str(request.user.is_authenticated()))
    print("Superuser: "  + str(request.user.is_superuser))
    print("Groups: "  + str(request.user.groups.count()))

    print("foo bar")

    """ /DEBUG INFO """

    if request.user.is_authenticated():
        if request.user.is_superuser:
            print("you can do and see anything")
            # _contacts = Contact.objects.all()
        else:

            if request.user.groups.count() == 0:
                print("no groups assigned")
            elif request.user.groups.count() == 1:
                print("exactly one group.. that's normal (=nice)")
            else:
                print("hm.. why do you have more than one group?!")
    else:
        print("non-auth")

    """ TODO remove this block.. """
    if request.user.is_authenticated():
        messages.success(request, "Welcome " + str(request.user))
    else:
        messages.error(request, "You do not have permission to access this site!")
    """ TODO remove this block.. """

    _contacts = Contact.objects.all()

    cdict = {"remote_user": get_remote_user(request)}
    cdict.update({"contacts": _contacts,
                  "view_name": view_name})
    return render(request, 'nmap/index.html', cdict)


def remote_user_logout(request):
    """remoe_user_logout(request)"""

    remote_user = get_remote_user(request)

    """ DEBUG INFO """

    print("full url: " + str(request.build_absolute_uri()))

    print("user: " + str(request.user))
    print("remote_user: " + str(remote_user))

    #print("get user remote user: " + get_user(remote_user))

    print("Authenticated: " +  str(request.user.is_authenticated()))

    print("Superuser: "  + str(request.user.is_superuser))
    print("Groups: "  + str(request.user.groups.count()))

    """ /DEBUG INFO """

    if not request.user.is_authenticated():
        print("not authenticated.. what are you doing here?!")
        return HttpResponse("Sorry - 403 Forbidden")

    if not remote_user:
        print("not remote user.. regular log out")

        logout(request)
        return redirect("{0}://{1}/".format(request.scheme, request.get_host()))

    else:
        print("remote user.. log out 'invalid'")
        return redirect("{0}://log_out_user:@{1}/nmap/logged_out".format(request.scheme,
                                                                         request.get_host()))


def remote_user_logged_out(request):
    """ """
    print("logged out and redirecting")
    return redirect("{0}://{1}/".format(request.scheme, request.get_host()))

""" Profile """


class Profile(LoginRequiredMixin, TemplateView):
    """Profile"""

    def get(self, request, username, *args, **kwargs):
        """get"""

        u = User.objects.get(username=get_remote_user(request))
        orgunits = u.orgunit_set.all()

        cdict = {"remote_user": get_remote_user(request)}
        cdict.update({"orgunits": orgunits})
        cdict.update({"username": username})
        return render(request, 'nmap/profile.html', cdict)


class NoPermission(LoginRequiredMixin, TemplateView):
    """NoPermission"""

    def get(self, request, *args, **kwargs):
        """get"""

        cdict = {"remote_user": get_remote_user(request)}
        return render(request, 'nmap/no_permission.html', cdict)


""" NWScanDB Models Start here """


class ScanView(LoginRequiredMixin, TemplateView):
    """Scan View"""


    def get(self, request, *args, **kwargs):
        """get"""
        template_name = "nmap/scan.html"

        u = User.objects.get(username=get_remote_user(request))
        org_units = u.orgunit_set.all()

        form = ScanForm(
            initial={
                'org_unit': org_units[0].id,
            }
        )

        form.fields['org_unit'].queryset = u.orgunit_set

        cdict = {}
        cdict.update({"form": form})
        cdict.update({"org_units": org_units})
        return render(request, template_name, cdict)



class TasksJsonView(PermissionRequiredMixin, TemplateView):
    """Task Json View

    Get a list of all tasks that the User is is allowed to see.
    Filter either for user id or for group (membership)
    Return result as JSON dump so that the progress bar can be drawn with AJAX

    """
    permission_required = "nmap.view_task"
    login_url = "/nmap/no_permission"

    def get(self, request, *args, **kwargs):
        """TODO: get current user/group for filter"""

        u = User.objects.get(username=get_remote_user(request))
        orgunits = u.orgunit_set.all()

        _result = NmapTask.get_tasks_status_as_dict(org_unit__in=orgunits)
        return HttpResponse(json.dumps(_result), content_type="application/json")


class TasksView(PermissionRequiredMixin, TemplateView):
    """Tasks View

    get and post

    """
    permission_required = "nmap.view_task"
    login_url = "/nmap/no_permission"

    def get(self, request, *args, **kwargs):
        """get"""
        template_name = "nmap/tasks.html"

        u = User.objects.get(username=get_remote_user(request))
        orgunits = u.orgunit_set.all()
        _nmap_task = NmapTask.objects.filter(org_unit__in=orgunits)

        cdict = {"remote_user": get_remote_user(request)}
        cdict.update({"orgunits": orgunits})
        cdict.update({"nmap_tasks": _nmap_task})
        return render(request, template_name, cdict)

    def post(self, request, *args, **kwargs):
        """post"""

        u = User.objects.get(username=get_remote_user(request))
        org_units = u.orgunit_set.all()

        form = ScanForm(request.POST)
        if not form.is_valid():
            template_name = "nmap/scan.html"
            form.fields['org_unit'].queryset = u.orgunit_set

            cdict = {}
            cdict.update({"form": form})
            cdict.update({"org_units": org_units})
            return render(request, template_name, cdict)

        print("Form is valid!")


        targets = form.cleaned_data["targets"]
        comment = form.cleaned_data['comment']

        no_ping = request.POST.get('no_ping', False)
        banner_detection = request.POST.get('banner_detection', False)
        os_detection = request.POST.get('os_detection', False)
        run_now = request.POST.get('run_now', False)

        if no_ping:
            print("no_ping was selected. ")
        if banner_detection:
            print("banner_detection was selected.")
        if os_detection:
            print("os_detection was selected.")
        if run_now or not run_now:
            print("run_now is currently disabled.")

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

        print("ports list")
        print(_portlist)

        if form.cleaned_data["top_ports"]:
            _top_portlist = "--top-ports " + str(form.cleaned_data["top_ports"])
        else:
            _top_portlist = ""

        print("top ports")
        print(_top_portlist)

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

        return redirect('/nmap/tasks/')


class TaskDelete(LoginRequiredMixin, TemplateView):
    """Tasks Delete"""

    def get(self, request, task_id, *args, **kwargs):
        try:
            _nmap_task = NmapTask.objects.get(task_id=task_id)
            _nmap_task.delete()
        except ObjectDoesNotExist:
            messages.error(request, "does not exist!")
            return render(request, 'accounts/login.html')

        return redirect('/nmap/tasks/')


class NmapReportsView(PermissionRequiredMixin, TemplateView):
    """NmapReports View takes task_id"""

    permission_required = "nmap.view_task"
    login_url = "/nmap/no_permission"

    def get(self, request, *args, **kwargs):

        """
        _nmap_report = NmapReportMeta.get_nmap_report_by_task_id(task_id)
        for scanned_host in _nmap_report.hosts:

            scanned_host.datetime_starttime = datetime.datetime.fromtimestamp(int(scanned_host.starttime))
            scanned_host.datetime_endtime = datetime.datetime.fromtimestamp(int(scanned_host.endtime))

            scanned_host.get_open_ports_count = len(scanned_host.get_open_ports())
        """
        template_name = "nmap/reports.html"

        u = User.objects.get(username=get_remote_user(request))
        orgunits = u.orgunit_set.all()
        nmap_reports = NmapReportMeta.objects.filter(org_unit__in=orgunits)

        paginator = Paginator(nmap_reports, 25)

        page = request.GET.get('page')

        try:
            items_paged = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items_paged = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items_paged = paginator.page(paginator.num_pages)

        cdict = {"remote_user": get_remote_user(request)}
        cdict.update({"items_paged": items_paged})

        return render(request, template_name, cdict)


class NmapReportView(LoginRequiredMixin, TemplateView):
    """NmapReport View takes task_id"""

    def get(self, request, task_id, *args, **kwargs):

        u = User.objects.get(username=get_remote_user(request))

        _nmap_report = NmapReportMeta.get_nmap_report_by_task_id(task_id, user_obj=u)
        for scanned_host in _nmap_report.hosts:

            scanned_host.datetime_starttime = datetime.datetime.fromtimestamp(int(scanned_host.starttime))
            scanned_host.datetime_endtime = datetime.datetime.fromtimestamp(int(scanned_host.endtime))

            scanned_host.get_open_ports_count = len(scanned_host.get_open_ports())

        cdict = {}
        cdict.update({"report": _nmap_report})
        return render(request, 'nmap/report.html', cdict)


class NmapReportIDView(LoginRequiredMixin, TemplateView):
    """NmapReportID View - same as NmapReportView but takes id instead of task_id """

    def get(self, request, id, *args, **kwargs):

        _nmap_report = NmapReportMeta.get_nmap_report_by_id(id)

        cdict = {}
        cdict.update({"report": _nmap_report})
        return render(request, 'nmap/report.html', cdict)


class ImportView(LoginRequiredMixin, TemplateView):
    """Import View"""

    def get(self, request, *args, **kwargs):
        """get"""
        template_name = "nmap/import.html"

        cdict = {}
        #cdict.update({"import": "import"})
        return render(request, template_name, cdict)

    def post(self, request, *args, **kwargs):
        """post"""

        template_name = "nmap/import_result.html"

        import_file = request.FILES['file']
        if import_file:
            book = Workbook(import_file) #Open xlsx file
            sheets = []
            for sheet in book:
                    print sheet.name
                    sheets.append(sheet)
            content = import_file.read()

            cdict = {}
            cdict.update({"sheets": sheets})
            return render(request, template_name, cdict)
        else:
            raise Exception("nmap_import failed")




"""
#@login_required
def scan(request):

    if request.user.is_authenticated():
        print(request.user)

    else:
        print("you will need to login")

    #user.has_perm('foo.add_bar')


    #user.has_perm('foo.add_bar')
    return render(request, 'nmap/scan.html')
"""


"""sample:
https://django.readthedocs.org/en/1.8.x/topics/class-based-views/intro.html#mixins-that-wrap-as-view
class MyFormView(View):
    form_class = MyForm
    initial = {'key': 'value'}
    template_name = 'form_template.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # <process form cleaned data>
            return HttpResponseRedirect('/success/')

        return render(request, self.template_name, {'form': form})
"""
