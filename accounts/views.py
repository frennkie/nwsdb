from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template import RequestContext
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .forms import LoginForm


def index(request):
    return redirect('login')


def user_login(request, form=None):
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
@login_required
def user_logout(request):
    # Since we know the user is logged in, we can now just log them out.
    logout(request)

    # Take the user back to the homepage.
    return redirect('/accounts/login/')

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
