from django.conf.urls import url
from . import views

# set namespace
app_name = 'nmap'

urlpatterns = [
    url(r'^$', views.Index.as_view(), name='index'),
    url(r'^changelog/$',
        views.Changelog.as_view(), name='changelog'),
    url(r'^scan/$',
        views.ScanView.as_view(), name='scan'),
    url(r'^jsontasks/$',
        views.TasksJsonView.as_view(), name='jsontasks'),
    url(r'^tasks/$',
        views.TasksView.as_view(), name='tasks'),
    url(r'^task/delete/(?P<task_id>[-\w]+)$',
        views.TaskDelete.as_view(), name='task_delete'),
    url(r'^reports$',
        views.NmapReportsView.as_view(), name='reports'),
    url(r'^import/$',
        views.ImportView.as_view(), name='import_view'),
    url(r'^import/xml/$',
        views.NmapXMLImport.as_view(), name='xml_import'),
    url(r'^services/$',
        views.NetworkServicesView.as_view(), name='services_view'),
    url(r'^services/get$',
        views.NetworkServicesGet.as_view(), name='services_view'),
    url(r'^report/([-\w]+)$',
        views.NmapReportView.as_view(), name='report_view'),
    url(r'^report/task_id/(?P<task_id>[-\w]+).xml$',
        views.NmapReportXMLView.as_view(), name='report_view_xml'),
    url(r'^report/task_id/get/(?P<task_id>[-\w]+).xml$',
        views.NmapReportXMLGet.as_view(), name='report_get_xml'),
    url(r'^report/task_id/(?P<task_id>[-\w]+)$',
        views.NmapReportView.as_view(), name='report_task_id_view'),
    url(r'^report/id/(?P<report_id>[0-9]+)$',
        views.NmapReportIDView.as_view(), name='report_id_view'),
]
