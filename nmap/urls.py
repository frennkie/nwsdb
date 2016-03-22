from django.conf.urls import url
from . import views
from .views import ScanView, TasksJsonView, TasksView, TaskDelete
from .views import NmapReportView, NmapReportIDView, NmapReportsView
from .views import Profile
#from .views import NoPermission
from .views import ImportView


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^profile/(?P<username>[-\w]+)/$', Profile.as_view(), name='profile'),
    url(r'^scan/$', ScanView.as_view(), name='scan'),
    url(r'^jsontasks/$', TasksJsonView.as_view(), name='jsontasks'),
    url(r'^tasks/$', TasksView.as_view(), name='tasks'),
    url(r'^task/delete/(?P<task_id>[-\w]+)$', TaskDelete.as_view(), name='task_delete'),
    url(r'^reports$', NmapReportsView.as_view(), name='reports'),
    url(r'^import/$', ImportView.as_view(), name='import_view'),
    url(r'^report/([-\w]+)$', NmapReportView.as_view(), name='nmapreport_view'),
    url(r'^report/task_id/(?P<task_id>[-\w]+)$', NmapReportView.as_view(), name='nmapreport_task_id_view'),
    url(r'^report/id/(?P<report_id>[0-9]+)$', NmapReportIDView.as_view(), name='nmapreport_id_view'),
]
