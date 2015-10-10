from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from .models import Contact


#@permission_required('polls.can_vote', login_url='/login/')
def index(request):
    _contacts = Contact.objects.all()
    context = {'contacts': _contacts}
    # settings.LOGIN_URL
    return render(request, 'nmap/nmap_index.html', context)


