from django.conf.urls import url, patterns

from . import views
from .views import DummyView

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
                       url(r'^dummy/$', DummyView.as_view(), name='dummy'),
                       )
