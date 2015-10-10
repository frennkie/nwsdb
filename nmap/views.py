from django.shortcuts import render
from django.http import HttpResponse
from .models import Contact


def index(request):
    contacts = Contact.objects
    context = {'contacts': contacts}
    return render(request, 'nmap/nmap_index.html', context)
