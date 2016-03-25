from django.conf.urls import url
from . import views

# set namespace
app_name = 'accounts'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^profile/(?P<username>[-\w]+)/$', views.Profile.as_view(), name='profile'),
    url(r'^login/$', views.UserLogin.as_view(), name='login'),
    url(r'^logout/$', views.UserLogout.as_view(), name='logout'),
]
