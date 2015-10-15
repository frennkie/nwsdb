from django.views.generic import TemplateView
from braces.views import MessageMixin, LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.core.urlresolvers import resolve
from django.contrib import messages
from django.contrib.auth import logout

import json
import datetime



#from django.contrib.auth.decorators import login_required

# start import from my models
from nmap.tasks import celery_nmap_scan
from .models import Contact, NmapTask, NmapReportMeta
from django import forms


"""
This is the standard layout for a authenticated view to a html template.
call with: url(r'^some/$', SomeView.as_view(), name='some_view'), :

class SomeView(LoginRequiredMixin, TemplateView):
    def get(self, request):

        some = SomeClass.objects.all()
        other_stuff = OtherStuff.objects.all()

        r_data = {}
        r_data.update({"some": some,
                       "other_stuff": other_stuff})
        return render(request, 'nmap/index.html', r_data)

"""

def remote_user_logout(request):
    """remoe_user_logout(request)"""


    try:
        remote_user = request.META['REMOTE_USER']
    except KeyError:
        remote_user = None

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
    print("logged out and redirecting")
    return redirect("{0}://{1}/".format(request.scheme, request.get_host()))


class Profile(LoginRequiredMixin, TemplateView):
    """Tasks Delete"""

    def get(self, request, username):
        """get"""

        r_data = {}
        r_data.update({"username": username})
        return render(request, 'nmap/profile.html', r_data)


def index(request):
    """index"""

    view_name = request.resolver_match.url_name
    print(view_name)

    try:
        remote_user = request.META['REMOTE_USER']
    except KeyError:
        remote_user = None

    """ DEBUG INFO """
    print("full url: " + str(request.build_absolute_uri()))

    print("user: " + str(request.user))
    print("remote_user: " + str(remote_user))

    #print("get user remote user: " + get_user(remote_user))

    print("Authenticated: " +  str(request.user.is_authenticated()))

    print("Superuser: "  + str(request.user.is_superuser))
    print("Groups: "  + str(request.user.groups.count()))

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

    _contacts = Contact.objects.all()

    r_data = {}

    r_data.update({"remote_user": remote_user,
                   "contacts": _contacts,
                   "view_name": view_name})
    return render(request, 'nmap/index.html', r_data)


class ScanView(LoginRequiredMixin, TemplateView):
    """Scan View"""
    template_name = "nmap/scan.html"


    def get(self, request, *args, **kwargs):
        """get"""
        if request.user.is_authenticated():
            messages.success(request, "Welcome " + str(request.user))
        else:
            messages.error(request, "You do not have permission to access this site!")

        r_data = {}
        r_data.update({"form": forms.Form})
        return render(request, 'nmap/scan.html', r_data)


class TasksJsonView(LoginRequiredMixin, TemplateView):
    """Task Json View

    Get a list of all tasks that the User is is allowed to see.
    Filter either for user id or for group (membership)
    Return result as JSON dump so that the progress bar can be drawn with AJAX

    """

    def get(self, request, *args, **kwargs):
        """TODO: get current user/group for filter"""
        _result = NmapTask.get_tasks_status_as_dict()
        return HttpResponse(json.dumps(_result), content_type="application/json")


class TasksView(LoginRequiredMixin, TemplateView):
    """Tasks View

    get and post

    """

    def get(self, request, *args, **kwargs):
        """get"""

        current_view = resolve(request.path)[0]
        print(current_view)



        #if not request.user.has_perm("nmap.view_task"):
        if not request.user.has_perm("nmap.stop_task"):
            messages.error(request, "You do not have permission to ")
            return render(request, 'nmap/tasks.html', {})
            #return redirect('/nmap/')



        # _nmap_tasks = NmapTask.find(user_id=user.id)
        _nmap_task = NmapTask.find()

        r_data = {}
        r_data.update({"nmap_tasks": _nmap_task})
        return render(request, 'nmap/tasks.html', r_data)

    def post(self, request):
        """post"""

        scantypes = [ "-sT", "-sT", "-sS", "-sA", "-sW", "-sM",
                "-sN", "-sF", "-sX", "-sU" ]

        if request.POST['targets']:
            targets = request.POST["targets"]
        else:
            return False

        if request.POST['comment']:
            comment = request.POST['comment']
        else:
            comment = ""

        """
        if request.POST['run_now']:
            run_now = True
        else:
            run_now = False
        """

        scani = int(request.POST['scantype']) if 'scantype' in request.POST else 0
        if 'ports' in request.POST and len(request.POST['ports']):
            portlist = "-p " + request.POST['ports']
        else:
            portlist = ''
        noping = '-P0' if 'noping' in request.POST else ''
        osdetect = "-O" if 'os' in request.POST else ''
        bannerdetect = "-sV" if 'banner' in request.POST else ''
        options = "{0} {1} {2} {3} {4}".format(scantypes[scani],
                                               portlist,
                                               noping,
                                               osdetect,
                                               bannerdetect)



        """ use either eta OR countdown! """

        """
        _c_eta = datetime.datetime.utcnow() + datetime.timedelta(seconds=0)
        _c_exp = datetime.datetime.utcnow() + CELERY_TASK_EXPIRES
        _celery_task = celery_nmap_scan.apply_async(eta=_c_eta,
                                                    expires=_c_exp,
                                                    kwargs={'targets': str(targets),
                                                            'options': str(options)})
        """
        _celery_task = celery_nmap_scan.apply_async(kwargs={'targets': str(targets),
                                                            'options': str(options)})

        #nt = NmapTask(user=request.user, task_id=_celery_task.id, comment=comment)
        nt = NmapTask(task_id=_celery_task.id, comment=comment)
        nt.save()

        return redirect('/nmap/tasks/')


class TaskDelete(LoginRequiredMixin, TemplateView):
    """Tasks Delete"""

    def get(self, request, task_id):
        try:
            _nmap_task = NmapTask.objects.get(task_id=task_id)
            _nmap_task.delete()
        except ObjectDoesNotExist:
            messages.error(request, "does not exist!")
            return render(request, 'accounts/login.html')

        return redirect('/nmap/tasks/')


class NmapReportView(LoginRequiredMixin, TemplateView):
    """NmapReport View takes task_id"""

    def get(self, request, task_id):

        _nmap_report = NmapReportMeta.get_nmap_report_by_task_id(task_id)
        for scanned_host in _nmap_report.hosts:

            scanned_host.datetime_starttime = datetime.datetime.fromtimestamp(int(scanned_host.starttime))
            scanned_host.datetime_endtime = datetime.datetime.fromtimestamp(int(scanned_host.endtime))

            scanned_host.get_open_ports_count = len(scanned_host.get_open_ports())

        r_data = {}
        r_data.update({"report": _nmap_report})
        return render(request, 'nmap/report.html', r_data)


class NmapReportIDView(LoginRequiredMixin, TemplateView):
    """NmapReportID View - same as NmapReportView but takes id instead of task_id """

    def get(self, request, id):

        _nmap_report = NmapReportMeta.get_nmap_report_by_id(id)

        r_data = {}
        r_data.update({"report": _nmap_report})
        return render(request, 'nmap/report.html', r_data)

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
