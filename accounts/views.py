
from django.conf import settings

from django.views.generic import TemplateView
from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages

from .forms import LoginForm
import logging
logger = logging.getLogger(__name__)


def index(request):
    return redirect('accounts:login')


class UserLogin(TemplateView):
    """UserLogin"""

    def get(self, request, *args, **kwargs):
        # get - context provides "username"
        context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        template_name = "accounts/login.html"

        # hu?
        view_name = request.resolver_match.url_name
        logger.debug(view_name)
        logger.debug("full url: " + str(request.build_absolute_uri()))

        """
        try:
            remote_user = request.META['REMOTE_USER']
        except KeyError:
            remote_user = None
        logger.debug("remote_user: " + str(remote_user))
        """

        logger.debug("user: " + str(request.user))

        # hu?

        _next = request.GET.get('next', False)
        if _next:
            logger.debug("Next View: {0}".format(_next))
            context.update({'form': LoginForm(initial={'next': _next})})
        else:
            context.update({'form': LoginForm()})

        return render(request, template_name, context)

    def post(self, request, *args, **kwargs):
        # post
        context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        template_name = "accounts/login.html"

        form = LoginForm(request.POST)
        if form.is_valid():
            # Gather the username and password provided by the user.
            # This information is obtained from the login form.
            username = request.POST.get('username', False)
            password = request.POST.get('password', False)

            # Use Django's machinery to attempt to see if the username/password
            # combination is valid - a User object is returned if it is.
            user = authenticate(username=username, password=password)

            _remember_me = request.POST.get('remember_me', False)
            if _remember_me == "on":
                logger.debug("remember_me set..  currently not implemented")

            # If we have a User object, the details are correct.
            # If None (Python's way of representing the absence of a value), no user
            # with matching credentials was found.
            if user:
                # Is the account active? It could have been disabled.
                if user.is_active:
                    # If the account is valid and active, we can log the user in.
                    # We'll send the user back to the homepage.
                    login(request, user)
                    logger.debug("logged in user: " + str(user))

                    # Check whether a POST contains a value for 'next' (next site/url)
                    _next = request.POST.get('next', False)
                    if _next:
                        logger.debug("Next View: {0}".format(_next))
                        return redirect(_next)
                    else:
                        return redirect(settings.LOGIN_REDIRECT_URL)

                else:
                    # An inactive account was used
                    messages.error(request, "This account is disabled.")
                    return render(request, self.template_name, context)
            else:
                # Bad login details were provided. So we can't log the user in.
                messages.error(request, "error: Invalid credentials!")

                _next = request.POST.get('next', False)
                if _next:
                    logger.debug("Next View: {0}".format(_next))
                    context.update({'form': LoginForm(initial={'next': _next})})
                else:
                    context.update({'form': LoginForm()})

                return render(request, template_name, context)

        else:
            # Check whether a POST contains a value for 'next' (next site)
            messages.error(request, "error: Invalid Form!")
            _next = request.POST.get('next', False)
            if _next:
                logger.debug("Next View: {0}".format(_next))
                context.update({'form': LoginForm(initial={'next': _next})})
            else:
                context.update({'form': LoginForm()})

            return render(request, self.template_name, context)


class UserLogout(LoginRequiredMixin, TemplateView):
    """UserLogout"""

    def get(self, request, *args, **kwargs):
        # get - context provides "username"
        # context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)

        logout(request)

        return redirect("index")


""" Profile """


class Profile(LoginRequiredMixin, TemplateView):
    """Profile"""

    def get(self, request, *args, **kwargs):
        # get - context provides "username"
        context = self.get_context_data(**kwargs)  # prepare context data (kwargs from URL)
        template_name = "nmap/profile.html"

        # u = User.objects.get(username=get_remote_user(request))
        u = User.objects.get(username=request.user)
        orgunits = u.orgunit_set.all()

        # context.update({"remote_user": get_remote_user(request)})
        # context.update({"remote_user": "fake_remote_user"})
        context.update({"orgunits": orgunits})
        context.update({"username": context["username"]})
        return render(request, template_name, context)
