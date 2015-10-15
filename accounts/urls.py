from django.conf.urls import include, url, patterns

from . import views

""" trailing slash seems important """
"""
urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.user_login, name='login'),
    url(r'^logout/$', views.remote_user_logout, name='logout'),
    url(r'^logged_out/$', views.remote_user_logged_out, name='logged out'),
)
"""
