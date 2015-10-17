from django.conf.urls import url, patterns

from . import views
from .views import ScanView, TasksJsonView, TasksView, TaskDelete
from .views import NmapReportView, NmapReportIDView
from .views import Profile, NoPermission

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^logout/$', views.remote_user_logout, name='logout'),
    url(r'^logged_out/$', views.remote_user_logged_out, name='logout'),
    url(r'^profile/([-\w]+)/$', Profile.as_view(), name='profile'),
    url(r'^no_permission/$', NoPermission.as_view(), name='no_permission'),
    url(r'^scan/$', ScanView.as_view(), name='scan'),
    url(r'^jsontasks/$', TasksJsonView.as_view(), name='jsontasks'),
    url(r'^tasks/$', TasksView.as_view(), name='tasks'),
    url(r'^task/delete/([-\w]+)$', TaskDelete.as_view(), name='task_delete'),
    url(r'^report/([-\w]+)$', NmapReportView.as_view(), name='nmapreport_view'),
    url(r'^report/task_id/([-\w]+)$', NmapReportView.as_view(), name='nmapreport_task_id_view'),
    url(r'^report/id/([-\w]+)$', NmapReportIDView.as_view(), name='nmapreport_id_view'),
)
