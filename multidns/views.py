from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView

from .models import Dummy

def index(request):
    """index"""

    #return render(request, 'nmap/index.html', cdict)
    return JsonResponse({"foo": "bar"})


class DummyView(TemplateView):
    """Dummy View"""

    def __init__(self):
        pass

    def get(self, request, *args, **kwargs):
        """get"""
        template_name = "multidns.html"

        """
        print(get_remote_user(request))
        all_users = User.objects.all()
        """

        """
        cdict = {}
        cdict.update({"form": form})
        cdict.update({"org_units": org_units})
        return render(request, template_name, cdict)
        """

        return JsonResponse({"hello": "world"})
