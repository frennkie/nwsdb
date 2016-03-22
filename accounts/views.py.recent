from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import RequestContext
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

from django.http import HttpResponseForbidden

from .forms import LoginForm

def index(request):
    return redirect('login')

"""
def remote_user_login(request, remote_user, next=None):
    login(request, remote_user)
    return True
"""

def user_login(request, form=None):

    view_name = request.resolver_match.url_name
    print(view_name)
    print("full url: " + str(request.build_absolute_uri()))

    try:
        remote_user = request.META['REMOTE_USER']
    except KeyError:
        remote_user = None

    print("user: " + str(request.user))
    print("remote_user: " + str(remote_user))


    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':

        form = LoginForm(data=request.POST)
        if form.is_valid():
            # Gather the username and password provided by the user.
            # This information is obtained from the login form.
            username = request.POST['username']
            password = request.POST['password']

            # Use Django's machinery to attempt to see if the username/password
            # combination is valid - a User object is returned if it is.
            user = authenticate(username=username, password=password)

            try:
                _remember_me = request.POST['remember_me']
                if _remember_me == "on":
                    print("yepp")
                else:
                    print("nope")
            except:
                print("not at all")

            # If we have a User object, the details are correct.
            # If None (Python's way of representing the absence of a value), no user
            # with matching credentials was found.
            if user:
                # Is the account active? It could have been disabled.
                if user.is_active:
                    # If the account is valid and active, we can log the user in.
                    # We'll send the user back to the homepage.
                    login(request, user)
                    print("logged in user: " + str(user))

                    # Check whether a POST contains a value for 'next' (next site)
                    try:
                        _next = request.POST['next']
                        return redirect(_next)
                    except:
                        return redirect(settings.LOGIN_REDIRECT_URL)

                else:
                    # An inactive account was used
                    messages.error(request, "This account is disabled.")
                    return render(request, 'accounts/login.html', r_data)
            else:
                # Bad login details were provided. So we can't log the user in.
                messages.error(request, "error: Invalid credentials!")

                try:
                    r_data = {'form': LoginForm(initial={'next': request.GET['next']})}
                except:
                    r_data = {'form': LoginForm()}

                return render(request, 'accounts/login.html', r_data)

                """
                print "Invalid credentials for user: {0}".format(username)
                return HttpResponse("Invalid login details supplied.")
                """

        else:
            # Check whether a POST contains a value for 'next' (next site)
            try:
                form.next = request.POST['next']
            except:
                pass

            r_data = {'form': form}
            return render(request, 'accounts/login.html', r_data)

    # The request is not a HTTP POST, so display the login form.
    else:
        try:
            r_data = {'form': LoginForm(initial={'next': request.GET['next']})}
        except:
            r_data = {'form': LoginForm()}

        return render(request, 'accounts/login.html', r_data)




# Use the login_required() decorator to ensure only those logged in can access the view.
#@login_required
def remote_user_logout(request):
    """
    user_logout(request)
    """

    try:
        remote_user = request.META['REMOTE_USER']
    except KeyError:
        remote_user = None

    if not request.user.is_authenticated():
        print("not authenticated.. what are you doing here?!")
        #return HttpResponseForbidden()
        return HttpResponse("Sorry - 403 Forbidden")

    if not remote_user:
        print("not remote user.. regular log out")

        logout(request)
        return redirect("{0}://{1}/".format(request.scheme, request.get_host()))

    else:
        print("remote user.. log out 'invalid'")
        return redirect("{0}://log_out_user:@{1}/nmap/logged_out".format(request.scheme,
                                                                         request.get_host()))


def remote_user_logged_out(request):
    return HttpResponse("logged out..  go to: foo")

"""
class MyFormView(View):
    form_class = MyForm
    initial = {'key': 'value'}
    template_name = 'form_template.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # <process form cleaned data>
            return HttpResponseRedirect('/success/')

        return render(request, self.template_name, {'form': form})
"""
