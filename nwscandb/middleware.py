
from django.conf import settings


class DevAddRemoteUserMiddleware(object):
    """ Custom Middleware that adds a REMOTE_USER header """
    def process_request(self, request):
        if settings.DEBUG and settings.DEV_ADD_REMOTE_ENABLED:
            request.META['REMOTE_USER'] = settings.DEV_ADD_REMOTE_USER
