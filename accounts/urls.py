from django.conf.urls import patterns, include, url

from . import views

""" trailing slash seems important """
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.user_login, name='login'),
    url(r'^logout/$', views.user_logout, name='logout'),
]
