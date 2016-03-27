# nmap Forms
from django import forms


class LoginForm(forms.Form):
    """Login Form
        TODO look into:
        https://docs.djangoproject.com/en/1.8/topics/forms/modelforms/
        https://docs.djangoproject.com/en/1.8/ref/forms/api/
        required is True by default
    """

    username = forms.CharField(label='',
                               max_length=100,
                               widget=forms.TextInput(attrs={'class': 'form-control',
                                                             'placeholder': 'Username',
                                                             'autofocus': True}))

    password = forms.CharField(label='',
                               max_length=100,
                               widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                 'placeholder': 'Password'}))

    next = forms.CharField(label='next', required=False, widget=forms.HiddenInput())
