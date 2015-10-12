# nmap Forms
from django import forms


class LoginForm(forms.Form):
    """Login Form
        TODO look into:
        https://docs.djangoproject.com/en/1.8/topics/forms/modelforms/
        https://docs.djangoproject.com/en/1.8/ref/forms/api/
        required is True by default
    """

    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', max_length=100, widget=forms.PasswordInput)

