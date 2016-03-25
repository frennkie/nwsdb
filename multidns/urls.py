from django.conf.urls import url
from . import views

# set namespace
app_name = 'multidns'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^dummy/$', views.DummyView.as_view(), name='dummy'),
]
