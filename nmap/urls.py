from django.conf.urls import url
from . import views
from .views import ScanView, TasksJsonView, TasksView, TaskDelete
from .views import NmapReportView, NmapReportIDView, NmapReportsView
from .views import NetworkServicesView, NetworkServicesGet
from .views import Profile
from .views import NmapReportXMLView, NmapReportXMLGet
from .views import ImportView, NmapXMLImport
#from .views import NoPermission



urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^profile/(?P<username>[-\w]+)/$', Profile.as_view(), name='profile'),
    url(r'^scan/$', ScanView.as_view(), name='scan'),
    url(r'^jsontasks/$', TasksJsonView.as_view(), name='jsontasks'),
    url(r'^tasks/$', TasksView.as_view(), name='tasks'),
    url(r'^task/delete/(?P<task_id>[-\w]+)$', TaskDelete.as_view(), name='task_delete'),
    url(r'^reports$', NmapReportsView.as_view(), name='reports'),
    url(r'^import/$', ImportView.as_view(), name='import_view'),
    url(r'^import/xml/$', NmapXMLImport.as_view(), name='nmap_xml_import'),
    url(r'^services/$', NetworkServicesView.as_view(), name='services_view'),
    url(r'^services/get$', NetworkServicesGet.as_view(), name='services_view'),
    url(r'^report/([-\w]+)$', NmapReportView.as_view(), name='nmapreport_view'),
    url(r'^report/task_id/(?P<task_id>[-\w]+).xml$', NmapReportXMLView.as_view(), name='nmap_report_view_xml'),
    url(r'^report/task_id/get/(?P<task_id>[-\w]+).xml$', NmapReportXMLGet.as_view(), name='nmap_report_get_xml'),
    url(r'^report/task_id/(?P<task_id>[-\w]+)$', NmapReportView.as_view(), name='nmapreport_task_id_view'),
    url(r'^report/id/(?P<report_id>[0-9]+)$', NmapReportIDView.as_view(), name='nmapreport_id_view'),
]
