from django.views.generic import TemplateView
from braces.views import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import RequestContext
from django.db.models import ObjectDoesNotExist


from django.shortcuts import render, redirect
import json
import datetime
#from django.template import RequestContext

#from django.contrib.auth.decorators import login_required

# start import from my models
from nmap.tasks import celery_nmap_scan
from .models import Contact, NmapTask, NmapReportMeta
from django import forms

#@login_required
def index(request):
    _contacts = Contact.objects.all()

    context = {'contacts': _contacts}
    return render(request, 'nmap/index.html', context)


class ScanView(LoginRequiredMixin, TemplateView):
    """Scan View"""
    template_name = "nmap/scan.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            print("Welcome " + str(request.user))
        else:
            print("you will need to login")

        return render(request, 'nmap/scan.html', {'form': forms.Form})


class TasksJsonView(LoginRequiredMixin, TemplateView):
    """Task Json View

    Get a list of all tasks that the User is is allowed to see.
    Filter either for user id or for group (membership)
    Return result as JSON dump so that the progress bar can be drawn with AJAX

    """

    def get(self, request):
        """TODO: get current user/group for filter"""
        _result = NmapTask.get_tasks_status_as_dict()
        return HttpResponse(json.dumps(_result), content_type="application/json")


class TasksView(LoginRequiredMixin, TemplateView):
    """Tasks View

    get and post

    """

    def get(self, request):
        """get"""
        #_nmap_tasks = NmapTask.find(user_id=user.id)

        context = {'nmap_tasks': NmapTask.find()}
        #return render_template('tasks.html', tasks=_nmap_tasks)

        return render(request, 'nmap/tasks.html', context)

    def post(self, request):
        """post"""

        scantypes = [ "-sT", "-sT", "-sS", "-sA", "-sW", "-sM",
                "-sN", "-sF", "-sX", "-sU" ]


        if request.POST['targets']:
            targets = request.POST["targets"]
        else:
            abort(401)

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
            print("does not exist")

        return redirect('/nmap/tasks/')


class NmapReportView(LoginRequiredMixin, TemplateView):
    """NmapReport View"""

    def get(self, request, task_id):
        _nmap_report = NmapReportMeta.get_nmap_report_by_task_id(task_id)
        print(_nmap_report)
        context = {'report': _nmap_report}
        return render(request, 'nmap/report.html', context)


class NmapReportIDView(LoginRequiredMixin, TemplateView):
    """NmapReportID View - same as NmapReportView but takes id instead of task_id """

    def get(self, request, id):
        _nmap_report = NmapReportMeta.get_nmap_report_by_id(id)
        context = {'report': _nmap_report}
        return render(request, 'nmap/report.html', context)


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
